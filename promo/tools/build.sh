#!/usr/bin/env bash
# Builds one film: cue list -> synthesized mix -> limiter + two-pass loudnorm -> frames -> mp4.
#   bash tools/build.sh <film dir> <output name> [draft | audio]
# audio rebuilds only the sound and remuxes it into the existing <output name>.mp4.
# The film dir holds index.html and timeline.js, plus sound.py when it has its own score;
# otherwise the tutorial score in shared/tutorial_sound.py is used.
set -euo pipefail
cd "$(dirname "$0")/.."
DIR=$1 NAME=$2 MODE=${3:-}
OUT=out/$DIR
mkdir -p "$OUT"

node tools/events.mjs "$DIR/timeline.js" "$OUT/events.json"
DUR=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["dur"])' "$OUT/events.json")
SOUND=$DIR/sound.py
[ -f "$SOUND" ] || SOUND=shared/tutorial_sound.py
python3 "$SOUND" "$OUT/events.json" "$OUT/mix_raw.wav"

# Peak-limit first so loudnorm can stay linear, then normalise to -14 LUFS / -1 dBTP in two passes.
ffmpeg -v error -y -i "$OUT/mix_raw.wav" -af "alimiter=limit=0.33:attack=3:release=90:level=false" "$OUT/mix_lim.wav"
MEASURE=$(ffmpeg -hide_banner -i "$OUT/mix_lim.wav" -af loudnorm=I=-14:TP=-1.0:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
read -r I TP LRA TH OFF < <(python3 -c 'import json,sys; m=json.loads(sys.argv[1]); print(m["input_i"], m["input_tp"], m["input_lra"], m["input_thresh"], m["target_offset"])' "$MEASURE")
# A last limiter catches any peak loudnorm could not keep under -1 dBTP (AAC adds a little overshoot).
ffmpeg -v error -y -i "$OUT/mix_lim.wav" -af "loudnorm=I=-14:TP=-1.0:LRA=11:measured_I=$I:measured_TP=$TP:measured_LRA=$LRA:measured_thresh=$TH:offset=$OFF:linear=true,alimiter=limit=0.7:attack=1:release=60:level=false" -ar 48000 "$OUT/mix.wav"

if [ "$MODE" = audio ]; then
  ffmpeg -v error -y -i "$OUT/$NAME.mp4" -i "$OUT/mix.wav" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart "$OUT/$NAME.remux.mp4"
  mv "$OUT/$NAME.remux.mp4" "$OUT/$NAME.mp4"
  exit 0
fi

if [ "$MODE" = draft ]; then
  node tools/render.mjs "$DIR/index.html" "$OUT/draft.mp4" --size 960x540 --fps 30 --duration "$DUR" --audio "$OUT/mix.wav" --crf 24
else
  node tools/render.mjs "$DIR/index.html" "$OUT/$NAME.mp4" --size 1920x1080 --fps 60 --duration "$DUR" --audio "$OUT/mix.wav" --crf 18
fi
