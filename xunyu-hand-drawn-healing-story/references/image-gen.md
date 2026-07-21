# 生图通道

| 能力 | 含义 |
|---|---|
| **生图** | 根据 prompt 写出 PNG |
| **写文件** | 保存到集目录素材夹 `{集号}-素材/` |
| **跑脚本** | 旁白 PNG、ffmpeg / smoke |
| **浏览器** | 可选 HTML 预览 |

流水线位置：[`pipeline.md`](pipeline.md) §3。画风锚点在 `assets/defaults.yaml` 的 `style_anchor_*` / `negative_prompt`。

---

## 与 mode 的关系

| 情况 | 行为 |
|---|---|
| `mode: smoke` 或 `channel: skip` | **不生图**；占位图或复用已有 `NN-bw/color.png` |
| `mode: full` + 有 key / 内置工具 | 按 `channel` 真生图 |
| `mode: full` 但无 key | 回退 smoke，并一行告知用户 |

**不要**为选通道单独开一轮追问（违反「最多 1 问」）。用户未指定时：`auto`；smoke 直接 skip。

---

## `image_gen.channel`

| 值 | 说明 |
|---|---|
| `auto` | 按优先级尝试；失败则 skip + 告知 |
| `cursor_generate_image` | 宿主内置生图（如 Cursor GenerateImage） |
| `openai_images` | OpenAI / 兼容 Images API |
| `http_api` | 自配 `http_api.base_url` + model |
| `skip` | 明确跳过（smoke / 用户供图） |

### `auto` 优先级

1. 本轮用户指定通道 
2. 宿主内置生图 
3. `OPENAI_API_KEY` / 兼容网关 
4. `IMAGE_GEN_API_KEY` + `http_api.base_url` 
5. → `skip`（占位或请用户供图）

---

## 密钥（禁止写入 skill 仓库）

1. 项目 `.env` 
2. `~/.config/xunyu-hand-drawn-healing-story/config.env` 
3. 环境变量 `OPENAI_API_KEY` / `IMAGE_GEN_API_KEY`

```yaml
# 项目 config.yaml（无密钥）
image_gen:
 channel: openai_images
 size: "1024x1792"
 require_bw_pair: true
 http_api:
 base_url: https://api.openai.com/v1
 model: gpt-image-1
```

---

## 成对输出（强制）

`require_bw_pair: true` / `bw_to_color.require_paired_assets: true` 时，每镜必须：

```text
{集号}-素材/01-color.png
{集号}-素材/01-bw.png
```

| 做法 | 说明 |
|---|---|
| 同构图两次生成 | color 用彩色锚；bw 用「同构图、仅墨线/灰度、无填色」 |
| 从 color 去色派生 | 可接受；保持构图与线稿一致 |
| smoke 占位 | `smoke_render.sh` 自动成对生成灰白占位 |

缺一对 → **停止合成**并打印缺失路径。

---

## Prompt 拼装（Full）

每镜推荐结构：

```text
[画面描述 from 分镜]
+ style_anchor_zh（或 en）
+ 角色一致性短句（服装/发型锁死）
+ 顶部大留白给后期叠字
```

负向：整段 `negative_prompt`。

硬约束：

- 长旁白**不烧进图**；图内最多 2 字标签（`in_image_label_max_chars`）。 
- 不要写实 / 3D / 照片 / 二次元大眼 / Q 版贴纸 / 复杂背景。 
- 竖屏 9:16；人物偏中下，顶部空给字。

---

## 用户已供图

```yaml
mode: full
image_gen:
 channel: skip
```

核对命名与成对后，直接进叠字 → 合成（[`pipeline.md`](pipeline.md) §4–5）。

---

## 失败回退

| 失败 | 动作 |
|---|---|
| API 报错 / 超时 | 换下一 `auto` 候选；全失败 → skip + 告知 |
| 单镜缺 bw 或 color | 停；列出路径 |
| 尺寸非竖图 | 缩放到 1080×1920（cover + crop），勿拉伸变形 |
