# 四种成片引擎 · 实现约定

> Skill 默认：`engine: video-use` 
> **选型对比（优点/缺点/适合谁）** → 根目录 [`README.md`](../README.md)「四种成片方式对比」。 
> **完整流水线步骤** → [`pipeline.md`](pipeline.md)。 
> Skill 根：`~/.cursor/skills-cursor/xunyu-hand-drawn-healing-story`（`$SKILL`）。

可选完整样本脚手架（含素材与 exports）：

```text
# 可选本地实测样本脚手架（与题材无关）
./samples/episode-01-four-engines/
```

复制时**不要**拷 `node_modules` / `out` / 大 mp4。

---

## 动效对齐规格（四种必须一致）

1. 每镜：横向逐渐揭示（wipe left→right，默认 **1.0s**） 
2. 先 bw，再约 **0.8s** 叠化到 color（可自 `bw_to_color.enabled: false` 关掉） 
3. 顶部旁白淡入（约 0.15s 起、0.45s 淡入） 
4. 1080×1920 @30fps；镜间**硬切**；默认 BGM **none** 
5. 素材命名：`NN-bw.png` / `NN-color.png`（`NN` 两位）

---

## 项目目录模板（任一引擎）

```text
白色极简手绘/{集号}-{短标题}/
├── config.yaml # engine: video-use | html | remotion | hyperframes
├── {集号}-分镜.md
├── shots.json # [{"id":1,"duration":5,"text":"..."}, ...]
├── {集号}-素材/ # 01-bw.png 01-color.png …
├── out/ # 中间产物
└── exports/ # 成片 mp4
```

`config.yaml` 示例：

```yaml
mode: full
engine: video-use
theme_id: "06"
wipe:
 duration_sec: 1.0
bw_to_color:
 enabled: true
 fade_duration_sec: 0.8
bgm:
 mode: none
```

---

## 1. video-use（默认）

### 实现

- 旁白：`scripts/make_captions.py` → `out/captions/cap_NN.png` 
- 全量合成：`scripts/render_ffmpeg.sh` 
 - `xfade=wipeleft` + color `fade` + caption `overlay` 
 - 环境变量：`WIPE_DUR` `COLOR_ST` `COLOR_DUR` `CRF` `SLUG` … 
- 测通：`scripts/smoke_render.sh`（缺图写占位，再走同一套 ffmpeg 链路）

### 命令

```bash
SKILL=~/.cursor/skills-cursor/xunyu-hand-drawn-healing-story

# —— Smoke（可无真图）——
bash "$SKILL/scripts/smoke_render.sh"

# —— Full ——
python "$SKILL/scripts/make_captions.py" --shots shots.json --out out/captions \
 --font "$SKILL/assets/fonts/ZCOOLKuaiLe-Regular.ttf"

ASSETS=./第01集-素材 OUT=./out EXPORTS=./exports \
SHOTS_JSON=./shots.json CAPTIONS=./out/captions SLUG=ep01 \
bash "$SKILL/scripts/render_ffmpeg.sh"
```

### 何时选

日常批量、视频号/抖音日更。Agent **未指定引擎时必须走这条**。

---

## 2. HTML / CSS / JS

### 实现

- CSS `mask-image` 线性渐变做 wipe 
- `.color` 层 `opacity` 做上色 
- `templates/html/` 为最小可运行骨架（需自备 `assets/NN-*.png`）

### 从 skill 模板

```bash
cp -R ~/.cursor/skills-cursor/xunyu-hand-drawn-healing-story/templates/html ./预览-html
# 编辑 main.js 的 SHOTS；素材 → ./预览-html/assets/
open ./预览-html/index.html
```

### 从四方式预览复制

```bash
SRC="./samples/episode-01-four-engines"
cp -R "$SRC/01-html" ./01-html
# 素材：指向或复制第01集-素材 到 01-html/assets/
```

### 何时选

只预览 / 调 wipe；`engine: html` 时**不要**默认跑 ffmpeg，除非用户同时要求成片。

---

## 3. Remotion

### 实现

- React + mask 与 HTML 同构 
- `templates/remotion/`：`package.json` + `src/`（**无** `node_modules`、无示例 PNG） 
- `public/` 必须放**实体** PNG（坏 symlink → 404）

### 命令

```bash
cp -R ~/.cursor/skills-cursor/xunyu-hand-drawn-healing-story/templates/remotion ./02-remotion
cd ./02-remotion
# 复制素材到 public/01-bw.png …
npm install
npm start
npm run render
# 超时：npx remotion render src/index.ts Episode out/ep.mp4 --codec=h264 --timeout=180000
```

### 从四方式预览

```bash
SRC="./samples/episode-01-four-engines"
rsync -a --exclude node_modules --exclude out "$SRC/02-remotion/" ./02-remotion/
cd ./02-remotion && npm install
```

### 何时选

`engine: remotion`；要厚码率母带或 React/CI 流水线。

---

## 4. Hyperframes

### 实现

- HTML 根节点需 `data-start="0"` 等契约 
- wipe 用 GSAP `clip-path`；字体用 `@font-face` 
- `templates/hyperframes/`：最小 `package.json` + 骨架 `index.html` + `hyperframes.json` 
- draft 可能 2× 像素 → 交付缩到 1080×1920

### 命令

```bash
cp -R ~/.cursor/skills-cursor/xunyu-hand-drawn-healing-story/templates/hyperframes ./03-hyperframes
cd ./03-hyperframes
# 素材放入 assets/
npm install
npm run check
npm run dev
npm run render
```

### 从四方式预览

```bash
SRC="./samples/episode-01-four-engines"
rsync -a --exclude node_modules --exclude '*.log' "$SRC/03-hyperframes/" ./03-hyperframes/
cd ./03-hyperframes && npm install
```

### 何时选

`engine: hyperframes`；要 Studio 时间轴精修时。

---

## Agent 分支伪代码

```text
engine = config.engine or "video-use"
if mode == "smoke" and engine == "video-use":
 smoke_render.sh → exports/
elif engine == "html":
 填充 templates/html → 打开浏览器；交付预览说明
elif engine == "remotion":
 填充 templates/remotion + public 素材 → npm render
elif engine == "hyperframes":
 填充 templates/hyperframes + assets → npm render
else: # video-use full
 make_captions.py → render_ffmpeg.sh → exports/
```

非法 `engine` 值 → 回退 `video-use` 并告知用户。

---

## 与其它 skill 边界

| Skill | 关系 |
|---|---|
| 本 skill（`xunyu-hand-drawn-healing-story`） | 本视觉规格 + 四引擎编排 |
| `video-use` | 通用底层；默认脚本已内化到 `scripts/` |
| `handdraw-story-video` | 好事八拍 / 另一模具，勿混 |
| `hand-drawn-styles` | 仅画风 prompt |
