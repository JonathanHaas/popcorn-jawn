# 🍿 Popcorn Jawn

A self-hosted media share page. When a movie finishes downloading in Radarr, it automatically gets uploaded to [gofile.io](https://gofile.io) and appears on a simple web page. Links expire after 10 days and drop off on their own — nothing to manage.

**Live at:** `popcorn.jawnhaas.xyz`

---

## How it works

1. `sync.py` runs on a cron every 30 minutes
2. It polls Radarr's history for completed downloads (since `sync_since` in `shares.json`)
3. New movies get uploaded to gofile.io and written to `shares.json`
4. `index.html` reads `shares.json` and renders active/expired shares

## Setup

### Requirements

- Python 3
- Radarr running locally
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
*/30 * * * * /home/haasj/shares/sync.py >> /home/haasj/shares/sync.log 2>&1
```

### Web server

Point a vhost at the `shares/` directory with `index.html` as the default. Example lighttpd config:

```
$HTTP["host"] == "popcorn.example.com" {
    server.document-root = "/home/user/shares"
    index-file.names = ( "index.html" )
    dir-listing.activate = "disable"
}
```

---

Made with ❤️ in Philadelphia
