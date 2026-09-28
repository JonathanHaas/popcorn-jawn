# 🍿 Popcorn Jawn

**Live at [popcorn.jawnhaas.xyz](https://popcorn.jawnhaas.xyz)**

A self-hosted media share page. When a movie finishes downloading in Radarr, it automatically gets uploaded to [gofile.io](https://gofile.io) and appears on a simple web page with poster thumbnails, Rotten Tomatoes scores, and IMDb ratings. Links expire after 10 days — nothing to manage.

Also includes a built-in movie request interface powered by Jellyseerr.

---

## How it works

1. `sync.py` runs on a cron every 30 minutes
2. It polls Radarr's history for completed downloads (since `sync_since` in `shares.json`)
3. New movies get looked up in Jellyseerr for poster/TMDB data, uploaded to gofile.io, and written to `shares.json`
4. `index.html` reads `shares.json` and renders active/expired shares with posters and ratings
5. The request search box queries Jellyseerr live via `arr-control` (keeps API keys server-side)

## Setup

### Stack

`index.html` is a single self-contained file — no build step, no bundler.

- **[Tailwind CSS](https://tailwindcss.com)** — loaded via CDN (`cdn.tailwindcss.com`). Utility classes handle all layout and spacing; custom styles in a `<style>` block cover the card design, shimmer animation, and theme colors.
- **[Alfa Slab One](https://fonts.google.com/specimen/Alfa+Slab+One)** + **Inter** via Google Fonts — display font for titles, Inter for body text.
- **Vanilla JS** — no framework. `fetch()` for API calls, `localStorage` for pending request state, CSS transitions for the accordion panels and shimmer.

### Requirements

- Python 3
- Radarr running locally
- Jellyseerr running locally (for posters, ratings, and movie requests)
- [arr-control](https://github.com/JonathanHaas/arr-control) running locally (proxies Jellyseerr + OMDB API calls)
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

Point a vhost at the `shares/` directory with `index.html` as the default. Example lighttpd config:

```
$HTTP["host"] == "popcorn.example.com" {
    server.document-root = "~/shares"
    index-file.names = ( "index.html" )
    dir-listing.activate = "disable"
}
```

The `/arr-control/seerr/` endpoints need to be proxied to your arr-control instance (default port 5401). See [arr-control](https://github.com/JonathanHaas/arr-control) for setup.

---

Made with ❤️ in Philadelphia
