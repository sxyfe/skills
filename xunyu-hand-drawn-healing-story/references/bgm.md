# BGM 配置说明

> **产品默认：成片静音（`bgm.mode: none`）。** 
> 配乐能力保留（`local` / `platform`），但不在默认流水线里烧进音轨。 
> 机器默认见 [`../assets/defaults.yaml`](../assets/defaults.yaml) 的 `bgm:` 段。

本 skill：**无配音**（`no_voiceover: true`）。旁白只靠顶部叠字。

---

## 三种模式（`bgm.mode`）

| 模式 | 成片音轨 | 含义 | 何时用 |
|---|---|---|---|
| **`none`（默认）** | 无 | 全程静音；发布端也可不加 | 日更默认、试片、版权最省事 |
| **`platform`** | 无（不混入文件） | 成片仍静音；**发布时**在视频号 / 抖音 / 剪映曲库选曲 | 要固定「后期配乐」流程、但不把 mp3 烧进仓库产物 |
| **`local`** | 混入 `bgm.local_path` | 合成时把本地音频压进 mp4 | 用户明确要求「成片就要带同一首 BGM」、多平台同轨 |

### 与 defaults 的关系

```yaml
bgm:
 mode: none # 默认；不要擅自改成 local
 local_path: null
 volume: 0.10
 note: "成片默认静音。用户在剪映/视频号/抖音曲库自行配乐。"
```

用户没提音乐 → **保持 `none`**，不要追问「要不要 BGM」。

---

## `platform`（功能保留 · 非默认）

1. 成片仍按静音导出（与 `none` 在文件层面相同）。 
2. 交付时多写一句：建议在视频号/抖音曲库搜：`温馨` · `治愈` · `钢琴独奏` · `指弹吉他`。 
3. 气质：软钢琴慢板 / 指弹；**无歌词、无鼓点**；听感不抢字。 
4. **不要**把网易云等未授权文件下载后假装「platform」。

适用：用户说「我到平台上自己配」或「用曲库」，但没给本地文件。

---

## `local`（功能保留 · 须用户明确要求）

仅当用户明确说「把这首音乐混进成片 / 给 local 路径」时启用。

### 配置

```yaml
bgm:
 mode: local
 local_path: "./audio/soft-piano.mp3" # 用户自备、已确认授权
 volume: 0.10 # 建议 8%–12%
```

### 混音注意

1. **授权**：可商用 / 平台允许二次上传；skill **不捆绑**任何商业曲目。 
2. 音量：`volume ≈ 0.10`，宁可偏轻，不抢叠字。 
3. 时间轴：以视频为主；音频循环或裁到片长；末镜可随 `last_shot_fade_out_sec` 一并降到 0。 
4. 导出后 `ffprobe` 确认有音轨；听感「几乎无鼓点」。 
5. Remotion/HTML 样本里的静音占位轨 **不算** BGM；要音乐须显式 `local`。

### ffmpeg 混轨示意（video-use 后处理）

```bash
# 在已有静音成片上混入 BGM（示例；按项目改路径）
ffmpeg -y -i exports/ep01.mp4 -i ./audio/soft-piano.mp3 \
 -filter_complex "[1:a]volume=0.10,afade=t=out:st=48:d=2[a]" \
 -map 0:v -map "[a]" -c:v copy -c:a aac -shortest \
 exports/ep01-with-bgm.mp4
```

（各引擎也可在自身时间轴挂音频；以用户指定引擎为准。）

---

## 版权（写给执行代理）

| 做 | 不做 |
|---|---|
| 默认 `none`；交付说明「平台后期自配」 | 擅自把未授权 mp3 烧进成片再跨平台分发 |
| `local` 仅用用户提供且确认授权的文件 | 在 skill 仓库提交音频二进制或付费曲链接冒充内置 |
| `platform` 只给曲库搜索建议 | 用「platform」名义去爬取流媒体 |

---

## Agent 决策速查

```text
用户未提音乐 → bgm.mode = none
用户说平台/曲库自配 → mode = platform（成片仍静音 + 文案建议）
用户给了文件/要烧进轨 → mode = local + local_path + volume≈0.10
用户说不要任何音乐 → none
```

流水线中的位置：合成之后、质检之前核对「是否静音符合配置」→ [`pipeline.md`](pipeline.md) §6–7。
