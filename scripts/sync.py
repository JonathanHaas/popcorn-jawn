#!/usr/bin/env python3
"""Poll Radarr for completed downloads and auto-upload to gofile.io."""

import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path

_dir = Path(__file__).parent
_root = _dir.parent
_cfg = json.loads((_root / "config.json").read_text())

RADARR_URL = _cfg["radarr_url"]
RADARR_KEY = _cfg["radarr_key"]
GOFILE_EXPIRY_DAYS = _cfg.get("gofile_expiry_days", 10)
DATA_FILE = _root / "public" / "shares.json"

SEERR_URL = "http://localhost:5055"
SEERR_KEY = "MTc4ODY0ODg0NTQ0MGM3N2M0OGIwLTFjNWUtNDU1MC04OWRmLWRjMWJhZjcwMWEyOQ=="

SONARR_URL = "http://localhost:8989"


def sonarr_api_key():
    return ET.parse(os.path.expanduser("~/.config/Sonarr/config.xml")).getroot().findtext("ApiKey")


def sonarr_get(path, **params):
    import urllib.request, urllib.parse
    qs = urllib.parse.urlencode({**params, "apiKey": sonarr_api_key()})
    url = f"{SONARR_URL}/api/v3/{path}?{qs}"
    with urllib.request.urlopen(urllib.request.Request(url)) as r:
        return json.load(r)


def radarr(path, **params):
    import urllib.request, urllib.parse
    qs = urllib.parse.urlencode(params)
    url = f"{RADARR_URL}/api/v3/{path}{'?' + qs if qs else ''}"
    req = urllib.request.Request(url, headers={"X-Api-Key": RADARR_KEY})
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def load_data():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text())
    now = datetime.now(timezone.utc).isoformat()
    return {"sync_since": now, "shares": []}


def save_data(data):
    DATA_FILE.write_text(json.dumps(data, indent=2))


def upload_to_gofile(filepath):
    import urllib.request
    server_resp = json.loads(urllib.request.urlopen("https://api.gofile.io/servers").read())
    server = server_resp["data"]["servers"][0]["name"]
    filename = os.path.basename(filepath)
    result = subprocess.run(
        ["curl", "-s", "-F", f"file=@{filepath};filename={filename}",
         f"https://{server}.gofile.io/contents/uploadfile"],
        capture_output=True, text=True, timeout=3600
    )
    resp = json.loads(result.stdout)
    if resp.get("status") != "ok":
        raise RuntimeError(f"gofile upload failed: {resp}")
    return resp["data"]["downloadPage"]


def get_movie_title(movie_id):
    movie = radarr(f"movie/{movie_id}")
    return movie.get("title", "Unknown"), movie.get("year", "")


def seerr_lookup(title, year):
    """Return (posterPath, tmdbId) for the best Jellyseerr movie match."""
    import urllib.request, urllib.parse
    req = urllib.request.Request(
        f"{SEERR_URL}/api/v1/search?query={urllib.parse.quote(title)}",
        headers={"X-Api-Key": SEERR_KEY},
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            results = json.load(r).get("results", [])
        movies = [r for r in results if r.get("mediaType") == "movie"]
        # prefer exact year match
        for res in movies:
            res_year = int((res.get("releaseDate") or "")[:4] or 0)
            if res_year == int(year or 0):
                return res.get("posterPath"), res.get("id")
        # fallback: first movie result
        if movies:
            return movies[0].get("posterPath"), movies[0].get("id")
    except Exception:
        pass
    return None, None


def sync_sonarr(data):
    known_ids = {s["sonarr_history_id"] for s in data["shares"] if s.get("sonarr_history_id")}
    sync_since = datetime.fromisoformat(data["sync_since"])

    history = sonarr_get(
        "history",
        pageSize=50,
        sortKey="date",
        sortDirection="descending",
        includeSeries="true",
        includeEpisode="true",
    )

    new_count = 0
    for record in history.get("records", []):
        if record.get("eventType") != "downloadFolderImported":
            continue
        rec_id = record["id"]
        if rec_id in known_ids:
            continue

        rec_date = datetime.fromisoformat(record["date"].replace("Z", "+00:00"))
        if rec_date < sync_since:
            continue

        filepath = record.get("data", {}).get("importedPath", "")
        if not filepath or not os.path.exists(filepath):
            continue

        series = record.get("series") or {}
        episode = record.get("episode") or {}
        show_title = series.get("title") or record.get("sourceTitle", "").split(".S")[0].replace(".", " ")
        season_num = episode.get("seasonNumber", 0)
        ep_num = episode.get("episodeNumber", 0)
        ep_title = episode.get("title", "")

        size_bytes = os.path.getsize(filepath)
        size_human = f"{size_bytes/1e9:.1f}G" if size_bytes >= 1e9 else f"{size_bytes/1e6:.0f}M"

        label = f"{show_title} S{season_num:02}E{ep_num:02}"
        print(f"Uploading: {label} [{size_human}]...")
        try:
            link = upload_to_gofile(filepath)
        except Exception as e:
            print(f"  ERROR: {e}", file=sys.stderr)
            continue

        now = datetime.now(timezone.utc)
        data["shares"].append({
            "sonarr_history_id": rec_id,
            "sonarr_series_id": record.get("seriesId"),
            "sonarr_episode_id": record.get("episodeId"),
            "media_type": "tv",
            "title": show_title,
            "season": season_num,
            "episode": ep_num,
            "episode_title": ep_title,
            "gofile_link": link,
            "filepath": filepath,
            "size_human": size_human,
            "size_bytes": size_bytes,
            "created": now.isoformat(),
            "expires": (now + timedelta(days=GOFILE_EXPIRY_DAYS)).isoformat(),
        })
        save_data(data)
        print(f"  Done: {link}")
        new_count += 1

    return new_count


def main():
    data = load_data()

    # Ensure sync_since is always persisted — set to now on first run or if stripped
    if "sync_since" not in data:
        data["sync_since"] = datetime.now(timezone.utc).isoformat()
        save_data(data)

    known_history_ids = {s["radarr_history_id"] for s in data["shares"] if s.get("radarr_history_id")}
    known_movie_ids = {s["radarr_movie_id"] for s in data["shares"] if s.get("radarr_movie_id")}

    sync_since = datetime.fromisoformat(data["sync_since"])
    history = radarr("history", eventType=3, pageSize=50, sortKey="date", sortDirection="descending")

    new_count = 0
    for record in history.get("records", []):
        rec_id = record["id"]
        if rec_id in known_history_ids or record["movieId"] in known_movie_ids:
            continue

        rec_date = datetime.fromisoformat(record["date"].replace("Z", "+00:00"))
        if rec_date < sync_since:
            continue

        filepath = record.get("data", {}).get("importedPath", "")
        if not filepath or not os.path.exists(filepath):
            continue

        movie_id = record["movieId"]
        title, year = get_movie_title(movie_id)
        size_bytes = os.path.getsize(filepath)
        size_human = f"{size_bytes / 1e9:.1f}G"
        poster_path, tmdb_id = seerr_lookup(title, year)

        print(f"Uploading: {title} ({year}) [{size_human}]...")
        try:
            link = upload_to_gofile(filepath)
        except Exception as e:
            print(f"  ERROR: {e}", file=sys.stderr)
            continue

        now = datetime.now(timezone.utc)
        data["shares"].append({
            "radarr_history_id": rec_id,
            "radarr_movie_id": movie_id,
            "title": title,
            "year": year,
            "tmdbId": tmdb_id,
            "posterPath": poster_path,
            "gofile_link": link,
            "filepath": filepath,
            "size_human": size_human,
            "size_bytes": size_bytes,
            "created": now.isoformat(),
            "expires": (now + timedelta(days=GOFILE_EXPIRY_DAYS)).isoformat(),
        })
        save_data(data)
        print(f"  Done: {link}")
        new_count += 1

        subprocess.run([
            "openclaw", "message", "send",
            "--channel", "telegram",
            "--target", "8880003956",
            "--message", f"🍿 {title} ({year}) is now on Popcorn Jawn\n{link}\nExpires in {GOFILE_EXPIRY_DAYS} days",
        ], capture_output=True)

    tv_count = sync_sonarr(data)
    print(f"Sync complete. {new_count} movie(s), {tv_count} TV episode(s) uploaded.")


if __name__ == "__main__":
    main()
