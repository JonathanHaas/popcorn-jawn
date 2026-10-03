#!/bin/bash
# Remux H.264 MKVs to MP4 for Roku direct play. Deletes MKV after successful conversion.
FFMPEG=/usr/lib/jellyfin-ffmpeg/ffmpeg
FFPROBE=/usr/lib/jellyfin-ffmpeg/ffprobe
LOG=/tmp/remux_batch.log

echo "=== Batch remux started $(date) ===" | tee -a "$LOG"

find /mnt/external/movies -name "*.mkv" | sort | while read mkv; do
  codec=$("$FFPROBE" -v error -select_streams v:0 -show_entries stream=codec_name -of csv=p=0 "$mkv" 2>/dev/null | tr -d ',')
  if [ "$codec" != "h264" ]; then
    echo "SKIP (${codec}): $mkv" | tee -a "$LOG"
    continue
  fi

  mp4="${mkv%.mkv}.mp4"

  # Skip if MP4 already exists and is a reasonable size
  if [ -f "$mp4" ]; then
    mkv_size=$(stat -c%s "$mkv")
    mp4_size=$(stat -c%s "$mp4")
    if [ "$mp4_size" -gt $((mkv_size / 2)) ]; then
      echo "ALREADY DONE: $mp4" | tee -a "$LOG"
      rm -f "$mkv" && echo "  Deleted MKV" | tee -a "$LOG"
      continue
    fi
  fi

  echo "REMUXING: $(basename "$mkv")" | tee -a "$LOG"
  "$FFMPEG" -i "$mkv" -c:v copy -c:a copy -c:s mov_text -map 0 \
    -movflags +faststart "$mp4" >> "$LOG" 2>&1

  if [ $? -eq 0 ] && [ -f "$mp4" ]; then
    mp4_size=$(stat -c%s "$mp4")
    mkv_size=$(stat -c%s "$mkv")
    if [ "$mp4_size" -gt $((mkv_size / 2)) ]; then
      rm -f "$mkv" && echo "  OK — deleted MKV ($(du -sh "$mp4" | cut -f1))" | tee -a "$LOG"
    else
      echo "  ERROR: MP4 too small, keeping MKV" | tee -a "$LOG"
      rm -f "$mp4"
    fi
  else
    echo "  ERROR: ffmpeg failed, keeping MKV" | tee -a "$LOG"
    rm -f "$mp4"
  fi
done

echo "=== Batch remux complete $(date) ===" | tee -a "$LOG"

# Trigger Jellyfin library refresh
curl -s -X POST "http://localhost:8096/Library/Refresh" \
  -H "Authorization: MediaBrowser Token=\"c04b33c24b2bfbc22375af3b064eb77fb8756619e5e55429ad82eff937a9406a\"" \
  && echo "Jellyfin library scan triggered" | tee -a "$LOG"
