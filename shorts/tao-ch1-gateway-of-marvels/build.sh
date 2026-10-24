#!/usr/bin/env bash
# Builds the Tao Te Ching Chap. 1 "The Gateway of Marvels" YouTube Short.
# Source: https://archive.org/details/arredondo-03-27-24-tao-te-ching-chap-1-the-gateway-of-marvels-3-27-2024
# Usage (from the repo root): shorts/tao-ch1-gateway-of-marvels/build.sh path/to/source.mp4
set -euo pipefail
SRC="$1"
DIR="$(cd "$(dirname "$0")" && pwd)"
SLUG="$(basename "$DIR")"
WORK="$(cd "$DIR/../.." && pwd)/.work/$SLUG"
mkdir -p "$WORK"
START=176.6   # "Chapter one…"
DUR=46.4      # through "…is the gateway of marvels." and its settle, before "So" at 223.5
CARD=4.0      # house end card, silent
XF=0.5        # 15-frame dissolve into the card, over the held last frame

python3 -I "$DIR/captions.py" "$START" "$DUR" "$WORK/captions.ass"
python3 -I "$DIR/endcard.py" "$CARD" "$WORK/endcard.mp4"

ffmpeg -y -ss "$START" -t "$DUR" -i "$SRC" -i "$WORK/endcard.mp4" -filter_complex "
  [0:v]split[a][b];
  [a]scale=-2:1920,crop=1080:1920,gblur=sigma=30,eq=brightness=-0.18:saturation=0.8[bg];
  [b]crop=440:480:250:0,scale=1080:1178:flags=lanczos,eq=contrast=1.04:saturation=1.05,format=yuva420p,geq=lum='lum(X,Y)':cb='cb(X,Y)':cr='cr(X,Y)':a='255*min(1,min(Y/90,(H-Y)/160))'[fg];
  [bg][fg]overlay=0:400,ass='$WORK/captions.ass',fade=t=in:st=0:d=0.4,fps=30,format=yuv420p,
    tpad=stop_mode=clone:stop_duration=$XF,settb=AVTB[main];
  [1:v]fps=30,format=yuv420p,settb=AVTB[card];
  [main][card]xfade=transition=fade:duration=$XF:offset=$DUR[v];
  [0:a]loudnorm=I=-14:TP=-1.5:LRA=11,afade=t=in:st=0:d=0.3,afade=t=out:st=$(echo "$DUR-0.4" | bc):d=0.4,
    apad=whole_dur=$(echo "$DUR+$CARD" | bc)[aud]" \
  -map "[v]" -map "[aud]" -r 30 -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart -t "$(echo "$DUR+$CARD" | bc)" "$DIR/$SLUG.mp4"
