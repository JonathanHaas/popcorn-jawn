# 🍿 Popcorn Jawn

**Live at [popcorn.jawnhaas.xyz](https://popcorn.jawnhaas.xyz)**

A self-hosted media share and request page. When a movie finishes downloading in Radarr, it automatically gets uploaded to [gofile.io](https://gofile.io) and appears on the page with poster thumbnails, Rotten Tomatoes scores, and IMDb ratings. Links expire after 10 days — nothing to manage.

Includes a full request interface for movies and TV shows powered by Jellyseerr.

---

## Features

- **Now Showing** — active shares with posters, file sizes, ratings, and days-remaining badges
- **Movie requests** — search and request movies directly; appears as a pending card while downloading
- **TV show requests** — season/episode accordion picker: expand any season to see episode names, check/uncheck individual episodes, request selected seasons
- **Activity drawer** — hamburger menu shows active SABnzbd downloads with progress/speed, recently imported TV episodes (Sonarr history), in-progress TV downloads, and the full Now Sharing list
- **Pending cards** — requested items show greyed-out in Now Showing until the cron picks them up; dismissable via ×
- **Past Showings** — expired shares remain visible in a history section
- **Adult content blocked** — at both search and request endpoints
- **Radarr import hook** — H264 MKV files are remuxed to MP4 immediately on import (no waiting for the nightly cron)

---

## How it works

1. `sync.py` runs on a cron every 30 minutes
2. It polls Radarr's history for completed downloads (since `sync_since` in `shares.json`)
3. New movies get looked up in Jellyseerr for poster/TMDB data, uploaded to gofile.io, and written to `shares.json`
4. `index.html` reads `shares.json` and renders active/expired shares with posters and ratings
5. The request search box queries Jellyseerr live via `arr-control` (keeps API keys server-side)
6. TV show requests hit a `/seasons` + `/episodes` endpoint to lazy-load episode lists per season before sending to Jellyseerr → Sonarr

---

## Setup

### Stack

`index.html` is a single self-contained file — no build step, no bundler.

- **[Tailwind CSS](https://tailwindcss.com)** — loaded via CDN. Utility classes handle layout; custom styles cover cards, shimmer animation, and theme colors.
- **[Alfa Slab One](https://fonts.google.com/specimen/Alfa+Slab+One)** + **Inter** via Google Fonts
- **Vanilla JS** — no framework. `fetch()` for API calls, `localStorage` for pending request state, CSS transitions for accordion panels and shimmer.

### Requirements

- Python 3
- Radarr running locally (movies)
- Sonarr running locally (TV shows)
- Jellyseerr running locally (posters, ratings, movie + TV requests)
- [arr-control](https://github.com/JonathanHaas/arr-control) running locally — proxies Jellyseerr, OMDB, and SABnzbd API calls; handles adult content blocking
- lighttpd (or any static file server)
- `curl` for gofile uploads

### Config

Copy `config.example.json` to `config.json` and fill in your values:

```json
{
  "radarr_url": "http://localhost:7878",
  "radarr_key": "your-radarr-api-key",
  "gofile_expiry_days": 10
}
```

Your Radarr API key is under **Settings → General → Security**.

### shares.json

Created automatically on first run. Contains a `sync_since` timestamp (only movies downloaded after this date get shared) and the `shares` array.

To initialize without sharing your entire Radarr history, create it manually:

```json
{
  "sync_since": "2024-01-01T00:00:00+00:00",
  "shares": []
}
```

### Cron

```
*/30 * * * * ~/shares/sync.py >> ~/shares/sync.log 2>&1
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

`scripts/radarr_remux.sh` remuxes H264 MKV files to MP4 immediately when Radarr imports them, so they're Roku-compatible without waiting for a nightly batch job. Add it as a **Custom Script** notification in Radarr → Settings → Connect.

---

Made with ❤️ in Philadelphia
