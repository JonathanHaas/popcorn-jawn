#!/bin/bash
# Radarr import hook: remux H264 MKV → MP4 immediately on import
# Radarr passes radarr_moviefile_path via environment variable

FFMPEG=/usr/lib/jellyfin-ffmpeg/ffmpeg
FFPROBE=/usr/lib/jellyfin-ffmpeg/ffprobe
JKEY="c04b33c24b2bfbc22375af3b064eb77fb8756619e5e55429ad82eff937a9406a"
LOG=/tmp/radarr_remux.log

echo "=== Radarr hook fired $(date) | event: $radarr_eventtype | file: $radarr_moviefile_path ===" >> "$LOG"

# Only act on Download events with an actual file
[ "$radarr_eventtype" = "Test" ] && exit 0
[ -z "$radarr_moviefile_path" ] && exit 0
[[ "$radarr_moviefile_path" != *.mkv ]] && exit 0
[ ! -f "$radarr_moviefile_path" ] && exit 0

MKV="$radarr_moviefile_path"

# Check video codec
codec=$("$FFPROBE" -v error -select_streams v:0 \
  -show_entries stream=codec_name -of csv=p=0 "$MKV" 2>/dev/null | tr -d ',')

echo "Codec: $codec | $MKV" >> "$LOG"

if [ "$codec" != "h264" ]; then
  echo "SKIP (not h264, codec=$codec)" >> "$LOG"
  exit 0
fi

MP4="${MKV%.mkv}.mp4"

echo "REMUXING: $(basename "$MKV")" >> "$LOG"

"$FFMPEG" -i "$MKV" -c:v copy -c:a copy -c:s mov_text -map 0 \
  -movflags +faststart "$MP4" >> "$LOG" 2>&1

if [ $? -eq 0 ] && [ -f "$MP4" ]; then
  mp4_size=$(stat -c%s "$MP4")
  mkv_size=$(stat -c%s "$MKV")
  if [ "$mp4_size" -gt $((mkv_size / 2)) ]; then
    rm -f "$MKV"
    echo "OK — remuxed and deleted MKV ($(du -sh "$MP4" | cut -f1))" >> "$LOG"
    # Trigger Jellyfin library refresh
    curl -s -X POST "http://localhost:8096/Library/Refresh" \
      -H "Authorization: MediaBrowser Token=\"$JKEY\"" >> "$LOG" 2>&1
    echo "Jellyfin scan triggered" >> "$LOG"
  else
    echo "ERROR: MP4 too small, keeping MKV" >> "$LOG"
    rm -f "$MP4"
  fi
else
  echo "ERROR: ffmpeg failed, keeping MKV" >> "$LOG"
  rm -f "$MP4"
fi
