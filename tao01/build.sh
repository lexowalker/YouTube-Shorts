#!/usr/bin/env bash
# Builds the Tao Te Ching Chap. 1 "The Gateway of Marvels" YouTube Short.
# Source: https://archive.org/details/arredondo-03-27-24-tao-te-ching-chap-1-the-gateway-of-marvels-3-27-2024
# Usage: tao01/build.sh path/to/source.mp4
set -euo pipefail
SRC="$1"
DIR="$(cd "$(dirname "$0")" && pwd)"
START=176.6   # "Chapter one…"
DUR=46.0      # through "…is the gateway of marvels."

ffmpeg -y -ss "$START" -t "$DUR" -i "$SRC" -filter_complex "
  [0:v]split[a][b];
  [a]scale=-2:1920,crop=1080:1920,gblur=sigma=30,eq=brightness=-0.18:saturation=0.8[bg];
  [b]crop=440:480:250:0,scale=1080:1178:flags=lanczos,eq=contrast=1.04:saturation=1.05,format=yuva420p,geq=lum='lum(X,Y)':cb='cb(X,Y)':cr='cr(X,Y)':a='255*min(1,min(Y/90,(H-Y)/160))'[fg];
  [bg][fg]overlay=0:400,ass='$DIR/captions.ass',
    fade=t=in:st=0:d=0.4,fade=t=out:st=$(echo "$DUR-0.8" | bc):d=0.8[v];
  [0:a]loudnorm=I=-14:TP=-1.5:LRA=11,afade=t=in:st=0:d=0.3,afade=t=out:st=$(echo "$DUR-0.8" | bc):d=0.8[aud]" \
  -map "[v]" -map "[aud]" -r 30 -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart "$DIR/tao01-gateway-of-marvels-short.mp4"
