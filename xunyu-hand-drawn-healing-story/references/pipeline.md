# 完整流水线说明书

> **与 SKILL.md 的分工** 
> - `SKILL.md`：自然语言入口、Smoke 决策树、缺省表（短）。 
> - **本文件**：选题 → 分镜 → 生图 → 叠字 → 四引擎合成 → 导出 → 质检的可操作全步骤（厚）。 
> 机器默认：[`../assets/defaults.yaml`](../assets/defaults.yaml)；键释义：[`defaults.md`](defaults.md)。

Skill 根：`~/.cursor/skills-cursor/xunyu-hand-drawn-healing-story`（下文记为 `$SKILL`）。

---

## 两条路径（先选路再执行）

| 路径 | 何时 | 生图 | 合成 | 交付 |
|---|---|---|---|---|
| **Smoke 测通** | 「测试 / 先跑通 / 无 key / 一句话试试」 | **跳过**；占位或复用已有 `NN-bw/color` | 默认 `smoke_render.sh` | 一行 `exports/*.mp4` |
| **Full 出片** | 明确要成片 / 有图 / 有 API | 按 [`image-gen.md`](image-gen.md) 成对真图 | `make_captions` → 四引擎之一 | 一行路径 + 双平台标题 |

未指定时：无 key 或测通语义 → **smoke**；否则 **full**。引擎未指定 → **`video-use`**。

---

## 0. 配置落地

1. 读 `$SKILL/assets/defaults.yaml`。 
2. 若集目录有 `config.yaml`，**浅合并**覆盖（只写要改的键）。 
3. 解析用户话，填入（不问也能定）：

| 项 | 缺省 |
|---|---|
| `theme_id` | `"02"`（时间与等待） |
| `target_duration_sec` | `50`（说「一分钟」→ 55–60） |
| `shot_count` | `7`（合法 6–9） |
| `engine` | `video-use` |
| `bgm.mode` | `none` |
| `mode` | `smoke` 或 `full`（见上） |

4. 在集目录写出 `config.yaml`（至少含 `mode` / `theme_id` / `engine` / `wipe` / `bgm`）。

**禁止**开跑时连环追问生图通道、wipe 毫秒、四引擎对比——细节下沉本目录其它 md。

---

## 1. 选题 / 叙事弧

1. 打开 [`themes.md`](themes.md)：用户点名 → 映射 `01`–`10`；未提 → **`02`**。 
2. 自拟主题也可，但必须保留四段弧与白底极简画风。 
3. 四段**必过**（禁止说教/金句升华结尾）：

| 段 | 作用 | 验收 |
|---|---|---|
| **身份钩** | 3 秒内立住人设反差 | 第一句旁白能单独当封面文案 |
| **压抑 / 等待** | 情绪下压 | 有空位 / 冷掉物件等可画锚点 |
| **小反转 / 小确幸** | 具体物件兑现 | 物件进分镜与生图，不空喊口号 |
| **可画面化余味** | 空镜/物件收束 | 不说教、不金句升华 |

4. 旁白：口语短句，每镜 1–2 行，单行 ≤18 字（见 [`typography.md`](typography.md)）。 
5. 同时起草：**视频号标题** + **抖音标题**（主题表里有例，可改写）。

---

## 2. 分镜表 + `shots.json`

### 2.1 Markdown 分镜（`{集号}-分镜.md`）

至少含下列列：

| 列 | 内容 |
|---|---|
| 镜号 | 1…N（N = `shot_count`，6–9） |
| 时长 | 秒；总和 ≈ `target_duration_sec`（±10%） |
| 屏幕旁白 | 后期叠字原文（可 `\n` 两行） |
| 画面描述 | 可直接拼进生图 prompt |
| 气泡/标签 | 图内 ≤2 字或「无」 |
| 运镜 | 微推 / 静止 / 淡出…（本模具以硬切+wipe 为主） |
| 叙事功能 | 钩 / 压 / 转 / 味 |

文末附：角色一致性（服装/发型一句锁死）、封面候选镜号、BGM 备注（默认静音）。

### 2.2 机器可读 `shots.json`

```json
[
 {"id": 1, "duration": 6, "text": "等的不是回复", "label": "等"},
 {"id": 2, "duration": 7, "text": "是那盏还亮着的灯"}
]
```

- `id`：从 1 起连续整数。 
- `duration`：秒，浮点可。 
- `text`：叠字；多行用 `\n`。 
- `label`：可选，smoke 占位图角落字。

默认 7 镜时长参考：`[6, 7, 7, 7, 8, 7, 8]`（和 ≈50）。镜数变化时由 Agent **重算**使总和贴近目标秒数。

### 2.3 集目录骨架

```text
白色极简手绘/{集号}-{短标题}/
├── config.yaml
├── {集号}-分镜.md
├── shots.json
├── {集号}-素材/ # NN-bw.png / NN-color.png
├── out/
│ ├── captions/ # cap_NN.png
│ └── shots/ # 单镜 mp4（video-use）
└── exports/{slug}.mp4
```

用户只要分镜、不要渲染 → **写完本节即停**（见对话脚本 C）。

---

## 3. 生图（仅 Full；Smoke 跳过）

细则：[`image-gen.md`](image-gen.md)。

### Smoke

- `mode: smoke` 或 `image_gen.channel: skip` → **不调 API**。 
- 跑 `scripts/smoke_render.sh` 时：缺图则自动写灰白占位成对 PNG；`REUSE_ASSETS=1`（默认）保留已有成对图。

### Full

1. `channel: auto` 按优先级尝试（用户指定 → 内置生图 → OpenAI → http_api → skip）。 
2. 每镜必须成对：`{集号}-素材/01-color.png` + `01-bw.png`（两位编号）。 
3. Prompt = `画面描述` + `style_anchor_zh`；负向 = `negative_prompt`。 
4. **长旁白不烧进图**；图内最多 2 字标签。 
5. 跨镜锁同一角色描述。 
6. `require_paired_assets: true` 时缺一对 → **停并报缺文件路径**。 
7. 无 key 却要 full → 回退 smoke，并一行告知用户。

密钥只进项目 `.env` 或 `~/.config/xunyu-hand-drawn-healing-story/config.env`，**永不进 skill 仓库**。

---

## 4. 叠字（旁白 PNG）

1. 读 [`typography.md`](typography.md)：圆润手写印刷体、`#222222`、顶距约 6.5%、lh≈1.7。 
2. 字体默认：`$SKILL/assets/fonts/ZCOOLKuaiLe-Regular.ttf`（OFL）。 
3. 命令（在集目录）：

```bash
python "$SKILL/scripts/make_captions.py" \
 --shots shots.json \
 --out out/captions \
 --font "$SKILL/assets/fonts/ZCOOLKuaiLe-Regular.ttf"
```

4. 产出：`out/captions/cap_01.png` … 与画幅同为 1080×1920 透明底。 
5. Smoke：`smoke_render.sh` 会代调 captions；也可先手跑本步。

HTML / Remotion / Hyperframes：用同一 ttf 的 `@font-face`，文案仍来自 `shots.json` 的 `text`（可不经 PNG，但观感应对齐）。

---

## 5. 合成动效（四引擎共规）

每镜时间轴（默认）：

```text
0s ──────── wipe left→right（1.0s）揭示整幅
0.85s ───── bw→color 叠化开始（长 0.8s）
0.15s ───── 旁白淡入开始（长 0.45s）
镜末 ────── 硬切到下一镜；末镜可再淡出 0.4s
```

- 画幅：1080×1920 @30fps；`hard_cut: true`。 
- BGM：默认 **none**（见 [`bgm.md`](bgm.md)）。 
- 关上色：`bw_to_color.enabled: false`（仍建议保留成对素材以免引擎报错）。

引擎选型对比 → 根目录 [`README.md`](../README.md)；实现命令 → [`engines.md`](engines.md)。

### 5.1 video-use（默认）

**Smoke：**

```bash
# 集目录内，已有 shots.json
bash "$SKILL/scripts/smoke_render.sh"
# 或指定：
# SHOTS_JSON=./shots.json ASSETS=./第01集-素材 SLUG=ep01 bash "$SKILL/scripts/smoke_render.sh"
```

**Full：**

```bash
python "$SKILL/scripts/make_captions.py" --shots shots.json --out out/captions \
 --font "$SKILL/assets/fonts/ZCOOLKuaiLe-Regular.ttf"

ASSETS=./第01集-素材 OUT=./out EXPORTS=./exports \
SHOTS_JSON=./shots.json CAPTIONS=./out/captions SLUG=ep01 \
WIPE_DUR=1 COLOR_ST=0.85 COLOR_DUR=0.8 CRF=18 \
bash "$SKILL/scripts/render_ffmpeg.sh"
```

环境变量 ↔ config：见 [`advanced.md`](advanced.md)。

### 5.2 html（仅预览）

```bash
cp -R "$SKILL/templates/html" ./预览-html
# 编辑 main.js 的 SHOTS；素材 → ./预览-html/assets/（NN-bw / NN-color）
open ./预览-html/index.html
```

`engine: html` → **不要**默认跑 ffmpeg。

### 5.3 remotion

```bash
cp -R "$SKILL/templates/remotion" ./02-remotion
cd ./02-remotion
# public/ 放实体 PNG（勿坏 symlink）
npm install && npm start # 或 npm run render
```

### 5.4 hyperframes

```bash
cp -R "$SKILL/templates/hyperframes" ./03-hyperframes
cd ./03-hyperframes
# assets/ 放素材
npm install && npm run check && npm run render
```

draft 可能 2× 像素 → 交付缩到 1080×1920。

### Agent 分支（执行时照抄）

```text
engine = config.engine or "video-use"
if mode == "smoke" and engine == "video-use":
 smoke_render.sh → exports/
elif engine == "html":
 templates/html → 浏览器预览
elif engine == "remotion":
 templates/remotion → npm render
elif engine == "hyperframes":
 templates/hyperframes → npm render
else:
 make_captions → render_ffmpeg → exports/
```

非法 `engine` → 回退 `video-use` 并告知。

---

## 6. 导出与双平台文案

1. 成片路径约定：`exports/{slug}.mp4`（或 `filename_pattern`）。 
2. 规格：H.264 · yuv420p · 1080×1920 · 30fps；默认**无音轨**。 
3. 交付回复**必须**含一行：`成片：…/exports/xxx.mp4`（html 则写预览目录）。 
4. 同时给出视频号标题 + 抖音标题（full / 正式交付时必给；纯 smoke 测通可简写）。 
5. 可选：`ffprobe` 核时长，写入回复或 checklist。

---

## 7. 质检

短清单见 [`release-checklist.md`](release-checklist.md)。执行代理在交付前至少核：

- [ ] 时长在目标 ±10%；镜数 6–9；与 `shots.json` 一致 
- [ ] 1080×1920，无黑边拉伸 
- [ ] wipe 可见；启用上色时能感知 bw→color 
- [ ] 旁白未烧进母图；字体为手写体而非宋/黑印刷 
- [ ] 成片静音（除非用户明确 `bgm.mode: local`） 
- [ ] 四段弧齐全；结尾非说教升华 
- [ ] 视频号 + 抖音标题（正式片） 
- [ ] 用户已看到**一行输出路径**

---

## 8. 推荐工作流（一句话串起来）

```text
themes 选题 → 分镜.md + shots.json + config.yaml
 →（smoke：占位）或（full：成对生图）
 → make_captions（或 smoke 内置）
 →（可选 html 调手感）→ video-use 出片
 → 偶发 remotion 提画质 / hyperframes Studio
 → 质检 + 一行路径 + 双标题
```

进阶调参、只出分镜、本地 BGM：[`advanced.md`](advanced.md) + [`bgm.md`](bgm.md)。
