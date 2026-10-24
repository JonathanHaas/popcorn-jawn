#!/bin/bash
# Remux H.264 MKVs to MP4 for Roku direct play. Deletes MKV after successful conversion.
# Re-encodes H.265/HEVC → H.264 using hardware (h264_v4l2m2m) with libx264 fallback.
FFMPEG=/usr/lib/jellyfin-ffmpeg/ffmpeg
FFPROBE=/usr/lib/jellyfin-ffmpeg/ffprobe
LOG=/tmp/remux_batch.log

echo "=== Batch remux started $(date) ===" | tee -a "$LOG"

encode_to_h264() {
  local input="$1"
  local output="$2"

  # Try hardware encoder first
  "$FFMPEG" -y -i "$input" \
    -c:v h264_v4l2m2m -b:v 4M -c:a copy -c:s mov_text -map 0 \
    -movflags +faststart "$output" >> "$LOG" 2>&1
  if [ $? -eq 0 ] && [ -f "$output" ]; then
    local out_size
    out_size=$(stat -c%s "$output")
    [ "$out_size" -gt 1048576 ] && return 0
    rm -f "$output"
  fi

  # Fallback: software encode
  echo "  hw encode failed, falling back to libx264" | tee -a "$LOG"
  "$FFMPEG" -y -i "$input" \
    -c:v libx264 -crf 18 -preset fast -c:a copy -c:s mov_text -map 0 \
    -movflags +faststart "$output" >> "$LOG" 2>&1
}

find /mnt/external/movies -name "*.mkv" -o -name "*.mp4" | sort | while read src; do
  codec=$("$FFPROBE" -v error -select_streams v:0 -show_entries stream=codec_name -of csv=p=0 "$src" 2>/dev/null | tr -d ',')
  ext="${src##*.}"
  mp4="${src%.*}.mp4"

  case "$codec" in
    h264)
      if [ "$ext" = "mp4" ]; then
        echo "SKIP (already h264 mp4): $(basename "$src")" | tee -a "$LOG"
        continue
      fi
      # Remux MKV → MP4, no re-encode
      if [ -f "$mp4" ]; then
        src_size=$(stat -c%s "$src")
        mp4_size=$(stat -c%s "$mp4")
        if [ "$mp4_size" -gt $((src_size / 2)) ]; then
          echo "ALREADY DONE: $(basename "$mp4")" | tee -a "$LOG"
          rm -f "$src" && echo "  Deleted MKV" | tee -a "$LOG"
          continue
        fi
      fi
      echo "REMUXING (h264): $(basename "$src")" | tee -a "$LOG"
      "$FFMPEG" -y -i "$src" -c:v copy -c:a copy -c:s mov_text -map 0 \
        -movflags +faststart "$mp4" >> "$LOG" 2>&1
      ;;

    hevc|h265)
      if [ -f "$mp4" ] && [ "$ext" = "mkv" ]; then
        src_size=$(stat -c%s "$src")
        mp4_size=$(stat -c%s "$mp4")
        if [ "$mp4_size" -gt $((src_size / 4)) ]; then
          echo "ALREADY DONE: $(basename "$mp4")" | tee -a "$LOG"
          rm -f "$src" && echo "  Deleted source" | tee -a "$LOG"
          continue
        fi
      fi
      echo "ENCODING (hevc→h264): $(basename "$src")" | tee -a "$LOG"
      encode_to_h264 "$src" "$mp4"
      ;;

    *)
      echo "SKIP (${codec}): $(basename "$src")" | tee -a "$LOG"
      continue
      ;;
  esac

  if [ $? -eq 0 ] && [ -f "$mp4" ]; then
    mp4_size=$(stat -c%s "$mp4")
    src_size=$(stat -c%s "$src")
    if [ "$mp4_size" -gt $((src_size / 4)) ]; then
      [ "$src" != "$mp4" ] && rm -f "$src" && echo "  OK — deleted source ($(du -sh "$mp4" | cut -f1))" | tee -a "$LOG"
    else
      echo "  ERROR: output too small, keeping source" | tee -a "$LOG"
      rm -f "$mp4"
    fi
  else
    echo "  ERROR: ffmpeg failed, keeping source" | tee -a "$LOG"
    rm -f "$mp4"
  fi
done

echo "=== Batch remux complete $(date) ===" | tee -a "$LOG"

# Trigger Jellyfin library refresh
curl -s -X POST "http://localhost:8096/Library/Refresh" \
  -H "Authorization: MediaBrowser Token=\"c04b33c24b2bfbc22375af3b064eb77fb8756619e5e55429ad82eff937a9406a\"" \
  && echo "Jellyfin library scan triggered" | tee -a "$LOG"
