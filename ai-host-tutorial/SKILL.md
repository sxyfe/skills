---
name: ai-host-tutorial
description: >
  Orchestrates AI talking-head tutorial videos as five tracks (host, real screen capture,
  generated B-roll, graphic overlays, burned-in captions) using job-state.json and timeline.json.
  Routes to tutorial-storyboard, rachel-digital-human-production, tutorial-screen-capture,
  ai-broll-lock, tutorial-composite, and yuwen-publish-precheck. Use when the user says
  口播教程、数字人教程、AI主题视频、剪映时间轴、五轨合成、/ai-host-tutorial, or wants a
  host + screen recording + B-roll explainer. Does not generate readable IDE or website UIs.
  Paid voice/avatar APIs stay behind a 15-second preview gate.
disable-model-invocation: true
---

# AI 口播教程（主编排）

你只做编排和门禁。分镜、配音口播、录屏清单、空镜、剪映时间轴分别交给子 skill。子 skill 禁止回读本文件。

显式调用：`/ai-host-tutorial` 或 `$ai-host-tutorial`。

## 开工前

1. 确认声音、肖像、脚本、成片用途已获授权。未确认就停。
2. 项目根目录由用户指定；没有就停，问一个路径。
3. 目录不存在则建：`inputs/` `inputs/screen/` `work/` `outputs/` `outputs/broll/`。
4. 没有 `work/job-state.json` 时运行：

```bash
python3 {baseDir}/scripts/init_job_state.py --project <项目名> --out work/job-state.json
```

`{baseDir}` = 本 SKILL.md 所在目录。契约见 [references/contract.md](references/contract.md)。安全边界见 [references/safety.md](references/safety.md)。

## 硬规则

- 教程里的 GitHub、终端、产品后台必须是真实录屏或截图。禁止用生成模型去画能读的 IDE / 网页。
- 口播必须先 15 秒预览，用户书面批准后再出全片。
- 录屏文件由用户放入 `inputs/screen/`。没有文件就停，写出缺哪些镜头。
- 合成只出剪映/CapCut 时间轴清单，不替用户导出成片、不代替点击发布。
- 付费 API（MiniMax / HeyGen 等）在本轮第一次调用前要用户点头。
- 配音响度：平均约 -12 dB，峰值 0 dB。写进 job-state 的 `loudness`。
- 不在 state 里写 API key、Authorization、签名 URL。
- 公开 skill 不绑定某张参考图、某个主题、某个对标账号。

## 阶段（按序，过门禁再往下）

改 `work/job-state.json` 的 `stage` 和对应 `gates.*`。已完成的阶段不要重跑；复用已有 `voice_id` / `video_id`。

### 0 收输入

最少要有 `inputs/script.md`。口播轨还要肖像和声音源（交给口播 skill 校验）。画幅默认 `3:4`（1080×1440）；用户说竖屏短视频则 `9:16`。

可选：用户要改开头 → 读 `/dbs-hook`；要查口播顺稿 → 读 `/dbs-script-flow`。这两步不是硬依赖。

`gates.script` 在用户认稿后改为 `approved`。

### 1 分镜

Read 并执行 `tutorial-storyboard`。要产出 `work/timeline.json`。停下来让用户看分镜表，点头后 `gates.storyboard = done`。

### 2 口播（配音 + 人像）

镜头里有 `type=host` 才跑。

1. 若本机有 `rachel-digital-human-production`：Read 并执行它。音频驱动人像，不要改走平台「文本 + 自带音色」。只做到 15 秒预览就停。
2. 若没有该 skill：停，告诉用户安装它，或自己把 `work/voiceover-full.mp3` 和 `outputs/host-full.mp4` 放到项目里。

`gates.host_preview = ready` 后必须等人批准。批准前禁止出全片。批准后继续口播 skill 的全片步骤；全片落盘后写 `tracks.host.full` / `tracks.host.audio`，`gates.host_full = done`。

### 3 录屏清单

镜头里有 `type=screen` 才跑。Read 并执行 `tutorial-screen-capture`。然后停，等人把文件放进 `inputs/screen/`。收齐后 `gates.screen = received`。

本阶段可与阶段 2 的「等人看预览」并行等，但不要在预览批准前去付费出全片。

### 4 空镜

镜头里有 `type=broll` 才跑。Read 并执行 `ai-broll-lock`。没有定妆图就停，问一张。用户说不做空镜 → `gates.broll = skipped`。

### 5 剪映时间轴

Read 并执行 `tutorial-composite`。产出 `outputs/jianying-edl.md`。`gates.composite = done`。

### 6 发布前检

若有 `yuwen-publish-precheck`：把口播稿和字幕交给它。没有该 skill 就跳过，并写明未做发布前检。`gates.precheck` 记 `done` 或 `skipped`。

## 调用规则

| 时机 | 去读 | 子 skill 写出 |
|---|---|---|
| 脚本已认 | `tutorial-storyboard` | `work/timeline.json` |
| 分镜已认且需要口播 | `rachel-digital-human-production` | `outputs/preview-15s.mp4` 等 |
| 分镜已认且需要录屏 | `tutorial-screen-capture` | `work/screen-shotlist.md` |
| 分镜已认且需要空镜 | `ai-broll-lock` | `outputs/broll/*.mp4` |
| 各轨文件齐 | `tutorial-composite` | `outputs/jianying-edl.md` |
| 清单已出 | `yuwen-publish-precheck` | 预检报告 |

缺子 skill 就停在当前阶段，给出安装名（`npx skills add sxyfe/skills@<name> -g -y`），不要临场发明一套替代流程。

## 三个人像系统（不要混成一个 prompt）

| 系统 | 用在哪 | 谁来做 |
|---|---|---|
| 写实口播窗 | 方窗 / 圆形 PiP / 半屏说话 | 口播 skill |
| 抠像姿态 | 托腮、举手、叠在终端上 | 用户实拍或口播 skill 的多段姿态；剪映抠像 |
| 生成空镜 | 4–8 秒隐喻画面，不必对口型 | `ai-broll-lock` |

## 对用户怎么说话

每个停点只说：现在停在哪、缺哪个文件、批准后我跑哪一步。不要一次抛出五个选择题。
