#!/usr/bin/env bash
# video-use / ffmpeg：横扫揭示 + bw→color + 旁白叠层 → 竖屏 mp4
#
# 用法（在集目录内）:
# ASSETS=./第01集-素材 OUT=./out EXPORTS=./exports \
# SHOTS_JSON=./shots.json CAPTIONS=./out/captions \
# bash /path/to/xunyu-hand-drawn-healing-story/scripts/render_ffmpeg.sh
#
# shots.json: [{"id":1,"duration":5}, ...]
# 素材命名: ASSETS/01-bw.png + ASSETS/01-color.png
# 旁白: CAPTIONS/cap_01.png（先跑 make_captions.py）
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ASSETS="${ASSETS:?set ASSETS to folder with NN-bw.png / NN-color.png}"
OUT="${OUT:-./out}"
EXPORTS="${EXPORTS:-./exports}"
SHOTS_JSON="${SHOTS_JSON:?set SHOTS_JSON}"
CAPTIONS="${CAPTIONS:-$OUT/captions}"
SLUG="${SLUG:-healing-story}"
WIPE_DUR="${WIPE_DUR:-1}"
COLOR_ST="${COLOR_ST:-0.85}"
COLOR_DUR="${COLOR_DUR:-0.8}"
CRF="${CRF:-18}"

# 绝对路径：concat demuxer 的相对路径相对 concat 文件所在目录
OUT="$(cd "$(dirname "$OUT")" && pwd)/$(basename "$OUT")"
EXPORTS="$(mkdir -p "$EXPORTS" && cd "$EXPORTS" && pwd)"
ASSETS="$(cd "$ASSETS" && pwd)"
CAPTIONS="$(mkdir -p "$CAPTIONS" && cd "$CAPTIONS" && pwd)"
SHOTS_JSON="$(cd "$(dirname "$SHOTS_JSON")" && pwd)/$(basename "$SHOTS_JSON")"

mkdir -p "$OUT/shots" "$EXPORTS"

python3 - "$SHOTS_JSON" <<'PY' >"$OUT/shots.tsv"
import json, sys
for row in json.loads(open(sys.argv[1], encoding="utf-8").read()):
 print(f"{int(row['id'])}\t{float(row['duration'])}")
PY

LIST="$OUT/concat.txt"
: > "$LIST"

while IFS=$'\t' read -r id dur; do
 pad=$(printf '%02d' "$id")
 bw="$ASSETS/${pad}-bw.png"
 color="$ASSETS/${pad}-color.png"
 cap="$CAPTIONS/cap_${pad}.png"
 shot_out="$OUT/shots/shot_${pad}.mp4"
 for f in "$bw" "$color" "$cap"; do
 [[ -f "$f" ]] || { echo "missing: $f" >&2; exit 1; }
 done

 echo "→ 镜 $id (${dur}s)"

 FILTER="\
[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,format=rgba,setpts=PTS-STARTPTS[bw];\
[1:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,format=rgba,setpts=PTS-STARTPTS[co];\
[co]fade=t=in:st=${COLOR_ST}:d=${COLOR_DUR}:alpha=1[cof];\
[bw][cof]overlay=format=auto[bl];\
color=c=white:s=1080x1920:d=${dur}:r=30,format=rgba,setpts=PTS-STARTPTS[bg];\
[bg][bl]xfade=transition=wipeleft:duration=${WIPE_DUR}:offset=0,format=rgba[w];\
[2:v]scale=1080:1920,format=rgba,fps=30,fade=t=in:st=0.15:d=0.45:alpha=1,setpts=PTS-STARTPTS[cap];\
[w][cap]overlay=0:0:format=auto,format=yuv420p,fps=30[vout]"

 ffmpeg -y -nostdin -hide_banner -loglevel error \
 -loop 1 -t "$dur" -r 30 -i "$bw" \
 -loop 1 -t "$dur" -r 30 -i "$color" \
 -loop 1 -t "$dur" -r 30 -i "$cap" \
 -filter_complex "$FILTER" \
 -map "[vout]" -t "$dur" -r 30 \
 -c:v libx264 -pix_fmt yuv420p -crf "$CRF" -preset veryfast \
 "$shot_out"

 # 相对 concat.txt（位于 OUT/）→ shots/shot_NN.mp4
 echo "file 'shots/shot_${pad}.mp4'" >> "$LIST"
done <"$OUT/shots.tsv"

# optional last-shot fade handled per-project; concat copy is enough for default
FINAL="$OUT/${SLUG}.mp4"
ffmpeg -y -nostdin -hide_banner -loglevel error -f concat -safe 0 -i "$LIST" -c copy "$FINAL"
cp -f "$FINAL" "$EXPORTS/${SLUG}.mp4"
echo "OK → $EXPORTS/${SLUG}.mp4"
ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$FINAL"

# silence unused
: "$SCRIPT_DIR"
