#!/usr/bin/env bash
# 12 frames sampled evenly across a video, tiled 4x3, for a one-glance review.
#   contact-sheet.sh video.mp4 [sheet.png]
set -euo pipefail
in="${1:?usage: contact-sheet.sh video.mp4 [sheet.png]}"
out="${2:-sheet.png}"
dur="$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$in")"
# Sample at 1/12 steps, offset half a step so no tile lands on a black first frame.
fps="$(awk -v d="$dur" 'BEGIN { printf "%.6f", 12.5 / d }')"
ffmpeg -y -v error -ss "$(awk -v d="$dur" 'BEGIN { printf "%.3f", d / 24 }')" -i "$in" \
  -vf "fps=$fps,scale=480:-1,drawtext=text='%{pts\:hms}':x=8:y=8:fontsize=16:fontcolor=white:box=1:boxcolor=black@0.5,tile=4x3" \
  -frames:v 1 "$out" 2>/dev/null \
|| ffmpeg -y -v error -ss "$(awk -v d="$dur" 'BEGIN { printf "%.3f", d / 24 }')" -i "$in" \
  -vf "fps=$fps,scale=480:-1,tile=4x3" -frames:v 1 "$out"
echo "$out"
