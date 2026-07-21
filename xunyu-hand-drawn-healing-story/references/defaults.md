# Defaults 完整释义

机器可读真源：[`../assets/defaults.yaml`](../assets/defaults.yaml)（`version: 3`）。

项目覆盖：在集目录写 `config.yaml`，**浅合并**（只写要改的键）。**禁止**把 API key 写进 yaml 或提交仓库。

下文按「键 → 默认 → 含义 / 何时改」列出**全部可配置项**。

---

## 运行模式

| 键 | 默认 | 释义 |
|---|---|---|
| `mode` | `smoke` | `smoke`：跳过真生图，占位/已有素材也能出短 mp4。`full`：按 image-gen 真生图后合成。无 key /「测试」「先跑通」→ 强制 smoke。 |

---

## 画幅 / 时长 / 分镜

| 键 | 默认 | 释义 |
|---|---|---|
| `aspect_ratio` | `"9:16"` | 竖屏比；与 width/height 一致。 |
| `width` / `height` | `1080` / `1920` | 导出像素。 |
| `fps` | `30` | 帧率。 |
| `target_duration_sec` | `50` | 目标片长（秒）。用户说「一分钟」→ 用 55–60。 |
| `shot_count` | `7` | 镜数；合法范围 **6–9**。 |
| `shot_durations_sec` | `[6,7,7,7,8,7,8]` | 各镜秒数；总和应 ≈ `target_duration_sec`。镜数变了由 Agent 重算。 |
| `hard_cut` | `true` | 镜间硬切（无叠化转场）。 |
| `default_theme_id` | `"02"` | 用户未指定主题时的主题 ID。 |
| `theme_id` | `null` | `null` → 用 `default_theme_id`；否则 `01`–`10` 或自拟说明。 |
| `platforms` | `["shipinhao","douyin"]` | 双平台标题都要产出。 |
| `visual_category` | `white_minimal_handdrawn_general` | 白色极简手绘（通用，主题不限）。 |

---

## 动效

### `wipe`

| 键 | 默认 | 释义 |
|---|---|---|
| `wipe.enabled` | `true` | 是否横向揭示。 |
| `wipe.direction` | `left_to_right` | 左→右；与 ffmpeg `wipeleft` / CSS mask 对齐。 |
| `wipe.duration_sec` | `1.0` | 揭示时长。用户说「wipe 慢一点」→ 如 `1.4`。渲染侧：`WIPE_DUR`。 |

### `bw_to_color`

| 键 | 默认 | 释义 |
|---|---|---|
| `bw_to_color.enabled` | `true` | 黑白→淡彩叠化。 |
| `bw_to_color.require_paired_assets` | `true` | 必须成对 `NN-bw` + `NN-color`；缺则停。smoke 占位仍成对。 |
| `bw_to_color.fade_start_sec` | `0.85` | 上色开始时刻。→ `COLOR_ST`。 |
| `bw_to_color.fade_duration_sec` | `0.8` | 上色叠化长度。→ `COLOR_DUR`。 |

### 旁白淡入 / 片尾

| 键 | 默认 | 释义 |
|---|---|---|
| `caption_fade_in.start_sec` | `0.15` | 旁白开始淡入。 |
| `caption_fade_in.duration_sec` | `0.45` | 旁白淡入时长。 |
| `last_shot_fade_out_sec` | `0.4` | 末镜淡出建议值（引擎实现程度不一）。 |

---

## 引擎

| 键 | 默认 | 释义 |
|---|---|---|
| `engine` | `video-use` | 成片引擎。合法值见下。 |
| `engine_allowed` | `[video-use, html, remotion, hyperframes]` | 白名单；非法值回退 `video-use`。 |

| `engine` 值 | 行为摘要 |
|---|---|
| `video-use` | 默认；`make_captions` + `render_ffmpeg`；smoke 用 `smoke_render.sh` |
| `html` | 浏览器预览，不强制 mp4 |
| `remotion` | React 帧精确渲染 |
| `hyperframes` | GSAP + Studio / CLI 出片 |

选型细节 → [`../README.md`](../README.md)；命令 → [`engines.md`](engines.md)。

---

## 导出 `export`

| 键 | 默认 | 释义 |
|---|---|---|
| `export.codec` | `h264` | 视频编码。 |
| `export.pixel_format` | `yuv420p` | 兼容短视频平台。 |
| `export.crf` | `18` | 质量（越小越清晰体积越大）。smoke 脚本默认偏 `23` 求快。→ `CRF`。 |
| `export.preset` | `veryfast` | ffmpeg x264 preset。 |
| `export.include_silent_audio` | `false` | 是否垫静音轨；默认不要（真静音）。 |
| `export.filename_pattern` | `"{slug}-ep{ep:02d}.mp4"` | 命名模板；脚本也可用 `SLUG` 简化为 `{slug}.mp4`。 |

---

## 生图 `image_gen`

| 键 | 默认 | 释义 |
|---|---|---|
| `image_gen.channel` | `auto` | `auto` \| `cursor_generate_image` \| `openai_images` \| `http_api` \| `skip`。详见 [`image-gen.md`](image-gen.md)。 |
| `image_gen.size` | `"1024x1792"` | 竖图建议尺寸（再裁/缩到 1080×1920）。 |
| `image_gen.require_bw_pair` | `true` | 每镜必须 bw+color。 |
| `image_gen.env_keys.openai` | `OPENAI_API_KEY` | OpenAI/兼容网关环境变量名。 |
| `image_gen.env_keys.generic` | `IMAGE_GEN_API_KEY` | 通用 HTTP 生图 key。 |
| `image_gen.config_paths` | `.env` 与 `~/.config/xunyu-hand-drawn-healing-story/config.env` | 密钥搜索路径。 |
| `image_gen.http_api.base_url` | `null` | 自建/兼容 API 根 URL。 |
| `image_gen.http_api.model` | `null` | 模型名。 |

### 画风锚点（长文本）

| 键 | 释义 |
|---|---|
| `style_anchor_zh` | 中文正向风格锚（白底、细抖墨线、稀疏填色、顶部留白叠字…）。 |
| `style_anchor_en` | 英文等价锚，给英文通道用。 |
| `negative_prompt` | 负向：写实/3D/二次元大眼/满涂/长句烧进图等。 |

---

## 字体 `typography`

| 键 | 默认 | 释义 |
|---|---|---|
| `typography.format` | `rounded_handwritten_print` | 圆润手写印刷体目标体感。 |
| `typography.color` | `#222222` | 字色。 |
| `typography.outline_color` | `#FFFFFF` | 描边色。 |
| `typography.outline_px` | `2` | 描边像素。 |
| `typography.size_px` | `42` | 字号。 |
| `typography.line_height` | `1.7` | 行距。 |
| `typography.letter_spacing_em` | `0.04` | 字距。 |
| `typography.align` | `center` | 水平对齐。 |
| `typography.position` | `top` | 垂直区域：顶部。 |
| `typography.top_ratio` | `0.065` | 距顶比例（画高）。 |
| `typography.max_lines_per_shot` | `2` | 每镜最多行数。 |
| `typography.max_chars_per_line` | `18` | 单行字数上限。 |
| `typography.in_image_label_max_chars` | `2` | 烧进图的标签上限。 |
| `typography.font_file` | `assets/fonts/ZCOOLKuaiLe-Regular.ttf` | 默认字体（相对 skill 根）。 |
| `typography.font_candidates` | 快乐体 → 别名 → 楷/宋系统回退 | 加载顺序；见 [`typography.md`](typography.md)。 |

---

## BGM `bgm`

| 键 | 默认 | 释义 |
|---|---|---|
| `bgm.mode` | `none` | **成片默认静音**。可选 `local` / `platform`，见 [`bgm.md`](bgm.md)。 |
| `bgm.local_path` | `null` | `mode: local` 时音频路径。 |
| `bgm.volume` | `0.10` | 本地混音建议音量（约 10%）。 |
| `bgm.note` | （说明串） | 提醒后期在剪映/视频号/抖音曲库自配。 |

---

## 叙事与输出布局

| 键 | 默认 | 释义 |
|---|---|---|
| `narrative_arc` | `[身份钩, 压抑/等待, 小反转/小确幸, 可画面化余味]` | 分镜必过四段。 |
| `forbid_preachy_ending` | `true` | 禁止说教/金句升华结尾。 |
| `no_voiceover` | `true` | 无配音；只有叠字。 |
| `output_layout.root` | `白色极简手绘/{集号}-{短标题}/` | 集目录根。 |
| `output_layout.files.storyboard` | `{集号}-分镜.md` | 分镜文件名。 |
| `output_layout.files.assets_dir` | `{集号}-素材/` | 素材夹。 |
| `output_layout.files.preview_dir` | `{集号}-预览/` | 预览夹（html 等）。 |
| `output_layout.files.exports_dir` | `exports/` | 成片夹。 |
| `output_layout.files.config` | `config.yaml` | 项目覆盖文件。 |

---

## 项目 `config.yaml` 示例

```yaml
mode: full
theme_id: "06"
shot_count: 9
target_duration_sec: 53
engine: video-use
wipe:
 duration_sec: 1.4
bw_to_color:
 enabled: true
 fade_duration_sec: 1.0
image_gen:
 channel: skip # 用户已供图时
bgm:
 mode: none # 或 local + local_path
```

完整步骤串起来 → [`pipeline.md`](pipeline.md)。
