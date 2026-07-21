---
name: xunyu-hand-drawn-healing-story
description: >
  手绘视频生成（xunyu）：自然语言一句话即可产出「白色极简手绘（通用）」竖屏短视频，主题不限。
  顶部叠字、左→右 wipe、可选黑白→淡彩，默认静音，默认引擎 video-use（ffmpeg）；
  另支持 Remotion / Hyperframes / HTML。支持 mode=smoke（占位图快速测通）与 mode=full。
  含 10 个通用示例主题池（可自拟覆盖）、完整流水线、四引擎、生图通道与 BGM 可选能力。
  Use whenever the user mentions 手绘视频、手绘竖屏、白色极简手绘、横扫上色、通用手绘短视频、
  视频号/抖音无配音叠字短视频、hand-drawn vertical shorts、xunyu 手绘、
  或要从示例主题池选题 / 自拟题材出片—even if they do not name this skill.
  Prefer this over generic video-use or handdraw-story-video for this white-minimal hand-drawn vertical format.
---

# xunyu · 手绘短视频（通用）

稳定 ID：`xunyu-hand-drawn-healing-story`。对外可称「手绘视频生成」。

视觉规格：**白色极简手绘（通用）**——主题不限，用户说什么题材就做什么。成片默认静音（BGM `none`）。

> **文档分层**
>
> - 本文件：自然语言入口 + Smoke 决策树（短）。
> - **完整能力与逐步出片** → `[references/pipeline.md](references/pipeline.md)`
> - **四引擎命令与分支** → `[references/engines.md](references/engines.md)`
> - 选型对比（优缺点）→ `[README.md](README.md)`

---

## 最小可测闭环（Smoke path）— 先读这个

目标：用户一句话 → **能出一条短 mp4**（或明确交付物路径）。

| 步 | 做什么 | 默认 |
| --- | -------------------------- | ---------------------------------------------------------------------- |
| 1 | 解析用户话 → 定 `theme_id` | 未提主题 → `02` **时间与等待** |
| 2 | 写分镜 md + `shots.json` | **6–9 镜**（`shot_count`，默认 7） |
| 3 | 生图 | `mode: smoke` → **跳过生图**，用占位图 / 已有素材目录；`full` 才真生图 |
| 4 | 合成 | 默认 **video-use**；无素材时 `scripts/smoke_render.sh` 也能出短 mp4 |
| 5 | 告诉用户 | **一行输出路径**（`exports/*.mp4` 或预览目录） |

```bash
# 集目录内一键 smoke（最少依赖：ffmpeg + Python/PIL）
# 安装后在 skill 根目录执行：
bash scripts/smoke_render.sh
# 或全局路径（视 Agent 安装位置而定）：
# bash ~/.agents/skills/xunyu-hand-drawn-healing-story/scripts/smoke_render.sh
```

---

## 自然语言入口（最多问 1 个问题）

用户说类似下面任意一句，**直接跑**，不要盘问：

- 「做一条手绘短视频」
- 「做一条 50 秒竖屏手绘视频，主题选时间与等待」
- 「用职场通勤题材做一条白色极简手绘短视频」
- 「大概一分钟的手绘短视频」

### 缺省规则（不问也行）

| 缺什么 | 用什么 |
| ------ | ------------------------------------------------------------- |
| 主题 | `theme_id: "02"`（时间与等待） |
| 时长 | ~50s（`target_duration_sec: 50`）；说「一分钟」→ 55–60s |
| 画幅 | 9:16 · 1080×1920 · 30fps |
| 引擎 | `video-use` |
| BGM | `none` |
| 模式 | 无 key / 用户说「测试」「先跑通」→ `mode: smoke`；否则 `full` |
| 镜数 | 6–9（默认 7） |

### 唯一可问的 1 个问题（仅当关键信息互相矛盾时）

例：同时说「只要预览」又「必须出 mp4」。否则 **0 问，直接 defaults 闭环**。

禁止开跑时追问生图通道、wipe 毫秒、四引擎对比——这些见 `references/`。

---

## 能力一览（细节下沉 references）

| 能力 | 默认 / 说明 | 详文 |
| ------------------- | ------------------------------------------------ | ---------------------------------------------------------------- |
| 自然语言出片 | 最多 1 问 + defaults | 本文件 |
| Smoke / Full | smoke 占位测通；full 真生图 | `[pipeline.md](references/pipeline.md)` |
| 10 示例主题（可自拟） | `01`–`10`；默认 `02`；任意题材可覆盖 | `[themes.md](references/themes.md)` |
| 四引擎 | 默认 video-use；另 html / remotion / hyperframes | `[engines.md](references/engines.md)` · `[README.md](README.md)` |
| 生图通道 | `auto` / 内置 / OpenAI / http_api / skip | `[image-gen.md](references/image-gen.md)` |
| 叠字字体 | OFL 站酷快乐体；无参考 PNG | `[typography.md](references/typography.md)` |
| BGM | 默认 **none**；可选 local / platform | `[bgm.md](references/bgm.md)` |
| 全量配置 | `assets/defaults.yaml` + 释义 | `[defaults.md](references/defaults.md)` |
| 高级调参 / 只出分镜 | wipe、镜数、engine 覆盖 | `[advanced.md](references/advanced.md)` |
| 发布自检 | 短清单 | `[release-checklist.md](references/release-checklist.md)` |
| 多 Agent | dbs-bridge 软链真源 | 文末 bridge |

---

## 对话脚本（用户说了什么 → 你做什么）

### A. 「做一条手绘短视频」/ 「大概一分钟」

1. `mode: smoke`（除非环境已有生图且用户要成品画质）
2. 选题默认 `02`；写 7 镜分镜 + `shots.json` + 双平台标题
3. `bash scripts/smoke_render.sh`（或项目内等价调用）
4. 回复一行：`成片：…/exports/xxx.mp4`

### B. 「主题用自我和解，engine 用 html 只要预览」

1. `theme_id: "06"`，`engine: html`
2. 写分镜 + 填 `templates/html` → `open index.html`
3. **不**跑 ffmpeg

### C. 「wipe 慢一点，出分镜不要渲染」

1. 只写分镜 + `shots.json` + `config.yaml`（`wipe.duration_sec: 1.4`）
2. 停。不生图、不合成

### D. 明确要成片 / 有图 / 有 API key

1. `mode: full` → 按 `[pipeline.md](references/pipeline.md)` + `[image-gen.md](references/image-gen.md)` 生图（成对 bw+color）
2. `make_captions.py` → `render_ffmpeg.sh`（或其它引擎）
3. 一行输出路径 + 双平台标题

---

## 默认摘要

| 项 | 默认 |
| ------ | ----------------------------------------------------- | ---------- | --------------- |
| 视觉规格 | 白色极简手绘（通用 · 主题不限） |
| 示例主题 | `references/themes.md`（01–10，可自拟覆盖） |
| 引擎 | **video-use**（`html` | `remotion` | `hyperframes`） |
| 字体 | OFL 站酷快乐体 `assets/fonts/ZCOOLKuaiLe-Regular.ttf` |
| 参考图 | **无**（skill 不附带对标 PNG） |
| BGM | **none** |
| 生图 | `image_gen.channel: auto`；smoke 可跳过 |

机器默认：`assets/defaults.yaml`。项目 `config.yaml` 浅合并覆盖。**密钥不进仓库。**

---

## 按需阅读

| 需要 | 文件 |
| ------------------------------ | -------------------------------------------------------------------- |
| **完整流水线（选题→质检）** | `[references/pipeline.md](references/pipeline.md)` |
| 全部配置项释义 | `[references/defaults.md](references/defaults.md)` |
| 选题 | `[references/themes.md](references/themes.md)` |
| 生图通道 | `[references/image-gen.md](references/image-gen.md)` |
| 四引擎实现 | `[references/engines.md](references/engines.md)` |
| 四引擎优缺点对比 | `[README.md](README.md)` |
| 叠字 | `[references/typography.md](references/typography.md)` |
| BGM（none / local / platform） | `[references/bgm.md](references/bgm.md)` |
| 高级调参 | `[references/advanced.md](references/advanced.md)` |
| 发布自检 | `[references/release-checklist.md](references/release-checklist.md)` |

---

## 引擎一览（细节下沉）

| `engine` | 动作 |
| -------------------------- | ------------------------------------------------------------------- |
| **video-use**（默认） | `make_captions.py` → `render_ffmpeg.sh`；smoke 用 `smoke_render.sh` |
| `html` | 填 `templates/html`，浏览器预览，不强制 mp4 |
| `remotion` / `hyperframes` | 见 `[references/engines.md](references/engines.md)` + `templates/` |

---

## 输出目录

```text
白色极简手绘/{集号}-{短标题}/
├── config.yaml
├── {集号}-分镜.md
├── shots.json
├── {集号}-素材/ # smoke 可为占位图
├── out/
└── exports/{slug}.mp4
```

交付时**必须**用一行写出最终路径。

---

## 边界

- 本 skill：白底极简手绘（**主题通用**）· 叠字 · wipe+上色 · 四引擎（默认 video-use）· NL 优先 + smoke。
- `handdraw-story-video`：好事八拍模具——勿混。
- `hand-drawn-styles`：只出画风 prompt。
- 通用 `video-use`：底层能力；白色极简手绘竖屏规格以本 skill 为准。

安装（skills.sh / GitHub）：

```bash
npx skills add sxyfe/skills@xunyu-hand-drawn-healing-story -g -y
```
