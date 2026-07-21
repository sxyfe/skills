#!/usr/bin/env bash
# smoke：最少依赖出短 mp4（占位图或已有素材）
#
# 在集目录内运行（需已有 shots.json），或：
# SHOTS_JSON=./shots.json ASSETS=./素材 bash smoke_render.sh
#
# 环境变量：
# SKILL skill 根目录（默认本脚本上级）
# ASSETS 素材目录（缺图时自动写占位 PNG）
# OUT 中间产物（默认 ./out）
# EXPORTS 成片目录（默认 ./exports）
# SLUG 文件名（默认 smoke）
# REUSE_ASSETS 若设为 1 且 ASSETS 已有成对图则不覆盖占位
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL="${SKILL:-$(cd "$SCRIPT_DIR/.." && pwd)}"
OUT="${OUT:-./out}"
EXPORTS="${EXPORTS:-./exports}"
SHOTS_JSON="${SHOTS_JSON:-./shots.json}"
ASSETS="${ASSETS:-./素材}"
CAPTIONS="${CAPTIONS:-$OUT/captions}"
SLUG="${SLUG:-smoke}"
REUSE_ASSETS="${REUSE_ASSETS:-1}"
WIPE_DUR="${WIPE_DUR:-1}"
COLOR_ST="${COLOR_ST:-0.85}"
COLOR_DUR="${COLOR_DUR:-0.8}"
CRF="${CRF:-23}"

if [[ ! -f "$SHOTS_JSON" ]]; then
 echo "missing shots.json: $SHOTS_JSON" >&2
 echo "先写 shots.json，例如 [{\"id\":1,\"duration\":5,\"text\":\"等的不是回复\"}]" >&2
 exit 1
fi

command -v ffmpeg >/dev/null || { echo "need ffmpeg" >&2; exit 1; }
command -v python3 >/dev/null || { echo "need python3" >&2; exit 1; }

mkdir -p "$ASSETS" "$OUT" "$EXPORTS"

# 缺图则生成灰白占位（bw=浅灰线框感，color=同构图略暖）
python3 - "$SHOTS_JSON" "$ASSETS" "$REUSE_ASSETS" <<'PY'
import json, sys
from pathlib import Path

shots = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assets = Path(sys.argv[2])
reuse = sys.argv[3] == "1"
assets.mkdir(parents=True, exist_ok=True)

try:
 from PIL import Image, ImageDraw, ImageFont
except ImportError:
 print("need Pillow: pip install Pillow", file=sys.stderr)
 sys.exit(1)

W, H = 1080, 1920
for row in shots:
 i = int(row["id"])
 pad = f"{i:02d}"
 bw_p = assets / f"{pad}-bw.png"
 co_p = assets / f"{pad}-color.png"
 if reuse and bw_p.exists() and co_p.exists():
 continue
 label = str(row.get("label") or row.get("text") or f"{i}")[:8]
 for path, bg, ink in (
 (bw_p, (245, 245, 245), (60, 60, 60)),
 (co_p, (252, 248, 242), (40, 70, 110)),
 ):
 im = Image.new("RGB", (W, H), bg)
 d = ImageDraw.Draw(im)
 # 极简物件占位：圆 + 横线 + 镜号
 cx, cy = W // 2, int(H * 0.58)
 d.ellipse((cx - 120, cy - 120, cx + 120, cy + 120), outline=ink, width=4)
 d.line((cx - 80, cy + 40, cx + 80, cy + 40), fill=ink, width=3)
 d.text((cx - 40, cy - 20), pad, fill=ink)
 d.text((80, int(H * 0.72)), label, fill=ink)
 im.save(path)
 print(f"placeholder → {bw_p.name} / {co_p.name}")
PY

FONT="$SKILL/assets/fonts/ZCOOLKuaiLe-Regular.ttf"
python3 "$SKILL/scripts/make_captions.py" \
 --shots "$SHOTS_JSON" \
 --out "$CAPTIONS" \
 ${FONT:+--font "$FONT"}

ASSETS="$ASSETS" OUT="$OUT" EXPORTS="$EXPORTS" \
SHOTS_JSON="$SHOTS_JSON" CAPTIONS="$CAPTIONS" SLUG="$SLUG" \
WIPE_DUR="$WIPE_DUR" COLOR_ST="$COLOR_ST" COLOR_DUR="$COLOR_DUR" CRF="$CRF" \
bash "$SKILL/scripts/render_ffmpeg.sh"

echo "SMOKE_OK → $EXPORTS/${SLUG}.mp4"
