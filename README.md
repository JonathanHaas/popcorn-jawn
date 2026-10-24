# 🍿 Popcorn Jawn

**Live at [popcorn.jawnhaas.xyz](https://popcorn.jawnhaas.xyz)**

A self-hosted media share and request page. When a movie or TV episode finishes downloading in Radarr/Sonarr, it automatically gets uploaded to [gofile.io](https://gofile.io) and appears on the page with poster thumbnails, Rotten Tomatoes scores, and IMDb ratings. Links expire after 7 days — nothing to manage.

Includes a full request interface for movies and TV shows powered by Jellyseerr.

---

## Features

- **Now Showing** — active shares with posters, file sizes, ratings, and days-remaining badges
- **Movie requests** — search and request movies directly; appears as a pending card while downloading
- **TV show requests** — season/episode accordion picker: expand any season to see episode names, check/uncheck individual episodes, request selected seasons; requested episodes auto-upload to gofile.io on import
- **TV episode cards** — downloaded episodes appear as Now Showing cards with episode badge (`S01E01`), episode title, synopsis, and a Get It download link
- **Activity drawer** — hamburger menu shows active SABnzbd downloads with progress/speed, recently imported TV episodes (Sonarr history) with gofile links, in-progress TV downloads, and the full Now Sharing list
- **Pending cards** — requested items show greyed-out in Now Showing until the cron picks them up; dismissable via ×
- **Delete** — deletes the gofile share, removes the entry, and deletes the file from disk (Radarr/Sonarr also updated)
- **Adult content blocked** — at both search and request endpoints

---

## Seasonal themes

The site automatically switches theme based on the current date:

| Theme | Active | Title |
|---|---|---|
| 🎃 Halloween | Oct 1–31 | Ghoulish Jawn |
| 🦃 Thanksgiving | Nov 1–30 | Gobbler Jawn |
| 🕎 Hanukkah | Dec 10–22 | Latke Jawn |
| 🎄 Christmas | Dec 1–Jan 7 | Fat Santa Jawn |
| 🍿 Default | rest of year | Popcorn Jawn |

Each theme has its own color palette, floating emoji, header icon, and OG social image. Themes are defined in `themes.json` — adding a new holiday is one JSON entry + running `generate_themes.py`.

### Adding a new theme

1. Add an entry to `themes.json` (copy any existing one, swap colors/text/emoji/date range)
2. Optionally add a `draw_<style>()` decorator function in `scripts/generate_themes.py` for a custom OG image icon
3. Run `python3 scripts/generate_themes.py` — OG images regenerate and the JS THEMES block in `index.html` updates automatically

---

## How it works

1. `sync.py` runs on a cron every 30 minutes
2. It polls Radarr's history for completed movie downloads (since `sync_since` in `shares.json`) and Sonarr's history for TV episodes
3. New items get looked up in Jellyseerr for poster/TMDB data, uploaded to gofile.io, and written to `shares.json`
4. `index.html` reads `shares.json` and renders active shares with posters and ratings
5. The request search box queries Jellyseerr live via `arr-control` (keeps API keys server-side)
6. `update_og.py` runs daily at midnight via cron — copies the seasonal OG image and rewrites `<title>` + Open Graph meta tags in `index.html` so crawlers (Slack, Facebook, iMessage) see the correct seasonal preview without running JS

---

## Setup

### Stack

`index.html` is a single self-contained file — no build step, no bundler.

- **[Tailwind CSS](https://tailwindcss.com)** — loaded via CDN
- **[Alfa Slab One](https://fonts.google.com/specimen/Alfa+Slab+One)** + **Inter** via Google Fonts
- **Vanilla JS** — no framework. `fetch()` for API calls, `localStorage` for pending request state

### Requirements

- Python 3 + Pillow (`pip install pillow`) for OG image generation
- Radarr running locally (movies)
- Sonarr running locally (TV shows)
- Jellyseerr running locally (posters, ratings, movie + TV requests)
- [arr-control](https://github.com/JonathanHaas/arr-control) running locally — proxies Jellyseerr, OMDB, and SABnzbd API calls; handles adult content blocking and delete endpoints
- lighttpd (or any static file server)
- `curl` for gofile uploads

### Config

Copy `config.example.json` to `config.json` and fill in your values:

```json
{
  "radarr_url": "http://localhost:7878",
  "radarr_key": "your-radarr-api-key",
  "jellyfin_url": "http://localhost:8096",
  "jellyfin_token": "your-jellyfin-api-key",
  "gofile_expiry_days": 7,
  "max_upload_bytes": 10737418240
}
```

Your Radarr API key is under **Settings → General → Security**.

### shares.json

Created automatically on first run. Contains a `sync_since` timestamp (only downloads after this date get shared) and the `shares` array.

To initialize without sharing your entire Radarr/Sonarr history, create it manually:

```json
{
  "sync_since": "2024-01-01T00:00:00+00:00",
  "shares": []
}
```

### Cron

```cron
*/30 * * * * ~/shares/scripts/sync.py >> ~/shares/sync.log 2>&1
0 0 * * * python3 ~/shares/scripts/update_og.py >> ~/shares/og.log 2>&1
```

### Web server

Point a vhost at the `public/` directory with `index.html` as the default. Example lighttpd config:

```
$HTTP["host"] == "popcorn.example.com" {
    server.document-root = "/home/user/shares/public"
    index-file.names = ( "index.html" )
    dir-listing.activate = "disable"
}
```

The `/arr-control/` endpoints need to be proxied to your arr-control instance (default port 5401). See [arr-control](https://github.com/JonathanHaas/arr-control) for setup.

### Radarr import hook (optional)

`scripts/radarr_remux.sh` remuxes H264 MKV files to MP4 immediately when Radarr imports them. Add it as a **Custom Script** notification in Radarr → Settings → Connect.

---

Made with ❤️ in Philadelphia
