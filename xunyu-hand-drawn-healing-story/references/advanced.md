# 高级配置（可选）

日常测通不必读本文件。用户明确要求调参 / 换引擎 / 本地 BGM / 只出分镜时再打开。

完整逐步流程 → [`pipeline.md`](pipeline.md)。全部键释义 → [`defaults.md`](defaults.md)。

---

## mode

| 值 | 行为 |
|---|---|
| `smoke`（默认测通） | 跳过真生图；占位图或复用 `ASSETS`；`smoke_render.sh` |
| `full` | 按 [`image-gen.md`](image-gen.md) 生图 → captions → ffmpeg / 其它引擎 |

无 API key、用户说「测试/先跑通」→ 强制 `smoke`。

---

## 可覆盖键（项目 config.yaml）

```yaml
mode: full
theme_id: "06"
shot_count: 9
target_duration_sec: 53
shot_durations_sec: [5, 6, 6, 6, 6, 6, 6, 6, 6] # 总和 ≈53
wipe:
 duration_sec: 1.4
bw_to_color:
 enabled: true
 fade_start_sec: 0.85
 fade_duration_sec: 1.0
engine: video-use # html | remotion | hyperframes
image_gen:
 channel: skip # 或 openai_images / http_api / cursor_generate_image
typography:
 size_px: 44
 top_ratio: 0.07
bgm:
 mode: none # 或 platform；或 local + local_path
 local_path: null
 volume: 0.10
export:
 crf: 18
```

浅合并：只写要改的键；其余继承 `assets/defaults.yaml`。

---

## 环境变量 ↔ config（video-use / smoke）

| config | `render_ffmpeg.sh` / `smoke_render.sh` |
|---|---|
| `wipe.duration_sec` | `WIPE_DUR` |
| `bw_to_color.fade_start_sec` | `COLOR_ST` |
| `bw_to_color.fade_duration_sec` | `COLOR_DUR` |
| `export.crf` | `CRF` |
| （文件名） | `SLUG` |
| （素材目录） | `ASSETS` |
| （成片目录） | `EXPORTS` |

示例：

```bash
WIPE_DUR=1.4 COLOR_DUR=1.0 CRF=20 SLUG=ep06 \
 bash "$SKILL/scripts/render_ffmpeg.sh"
```

---

## 只出分镜不渲染

用户说「只要分镜 / 不要渲染」→ 写：

1. `{集号}-分镜.md` 
2. `shots.json` 
3. `config.yaml`（含用户要的 wipe / theme / duration）

然后**停止**。不生图、不 `smoke_render`、不 `npm render`。

---

## 换引擎而不改分镜

同一套 `shots.json` + 素材可喂四引擎：

1. 改 `config.yaml` 的 `engine` 
2. 按 [`engines.md`](engines.md) 复制对应 `templates/` 
3. html → 只预览；其余 → 出 `exports/` 或引擎 `out/`

动效参数（wipe / 上色秒数）应在各引擎侧改到与 config 一致。

---

## BGM

默认 `none`。仅用户明确要求时用 `local`（自备授权文件）或声明 `platform`（成片仍静音、发布曲库自配）。

完整说明 → [`bgm.md`](bgm.md)（**不是**一句指针；模式/音量/版权/混轨示例均在该文件）。

---

## 镜数与时长重算

- 合法镜数：**6–9**。 
- 改 `shot_count` 后必须重写 `shot_durations_sec`，使总和 ≈ `target_duration_sec`（允许 ±10%）。 
- 旁白句数应能铺满镜数；宁可两镜共用情绪段，也不要灌说教金句凑句。

---

## 关掉上色

```yaml
bw_to_color:
 enabled: false
```

仍建议保留成对素材（部分模板假定双层）。纯线稿片可将 color 做成与 bw 相同文件。

---

## 默认索引

| 文件 | 用途 |
|---|---|
| [`../assets/defaults.yaml`](../assets/defaults.yaml) | 机器默认真源 |
| [`defaults.md`](defaults.md) | 人类可读全键释义 |
| [`pipeline.md`](pipeline.md) | 端到端步骤 |
| [`release-checklist.md`](release-checklist.md) | 交付前短检 |
