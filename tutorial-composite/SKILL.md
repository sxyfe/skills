---
name: tutorial-composite
description: >
  Assembles a CapCut/Jianying layer timeline (EDL markdown) from timeline.json plus host,
  screen, and B-roll assets. Use when ai-host-tutorial is ready to cut, or the user says
  剪映时间轴、jianying-edl、五轨合成清单、/tutorial-composite. Does not export the final mp4
  and does not click publish.
disable-model-invocation: true
---

# 剪映时间轴清单

输入：`work/timeline.json`、已齐的口播/录屏/空镜文件、`work/job-state.json` 的 `aspect`。  
输出：`outputs/jianying-edl.md`。  
禁止回读主编排 skill。禁止替用户导出、禁止代发。

## 开工检查

缺下面任一文件就停，列出缺项：

- `type=host` 且 `gates.host_full` 未完成，并且没有 `tracks.host.full` 或 `outputs/host-full.mp4`
- `type=screen` 且对应 `inputs/screen/` 文件不存在
- `type=broll` 且 `gates.broll` 不是 `done` 或 `skipped`（skipped 的镜头在清单里改用纯色底板）

配音轨优先用 `work/voiceover-full.mp3`。没有则写「用口播成片自带音，关掉其他视频音」。

## 图层（从底到顶）

| 轨 | 放什么 |
|---|---|
| V1 底板 | 纯色 / 点阵 / 用户指定底板。不要生成带字的 UI |
| V2 证据 | `screen` 录屏或截图，按镜裁切 |
| V3 口播 | 方窗或圆形蒙版；`visual` 写了抠像则去底后叠在 V2 上 |
| V4 贴图 | `gfx`：技巧条、键帽、箭头、吉祥物 |
| V5 字幕 | 硬字幕，对齐 `vo_text` 句界 |
| A1 配音 | 唯一人声音轨。空镜视频静音 |

画幅：`3:4` → 1080×1440；`9:16` → 1080×1920；`16:9` → 1920×1080。

口播窗默认：竖屏/3:4 放画面上三分之一，正方形或圆形，描边用用户已有模板色；用户没给模板就写「浅色描边 + 居中」。

## 写出 jianying-edl.md

1. 片头：项目名、画幅、总时长、响度目标（平均 -12 dB，峰值 0 dB）。
2. 素材表：轨、镜头 id、入点出点、文件路径、是否静音、蒙版。
3. 按时间顺序列每条操作，剪映里能照着拖。
4. 字幕表：起止秒、原文。烧进画面，不要依赖平台软字幕。
5. `gates.composite = done`，`tracks.composite.edl` 指向该文件。

## 清单正文结构

```markdown
# 剪映时间轴

画幅：1080×1440
时长：00:01:30
配音：work/voiceover-full.mp3（平均 -12 dB）

## 素材

| 轨 | 入点 | 出点 | 文件 | 备注 |
|---|---|---|---|---|
| A1 | 0.0 | 90.0 | work/voiceover-full.mp3 | 唯一人声 |
| V3 | 0.0 | 4.0 | outputs/host-full.mp4 | 圆形窗，静音 |

## 字幕

| 入点 | 出点 | 文案 |
|---|---|---|
| 0.0 | 4.0 | … |
```

入点出点用秒，保留一位小数，与 timeline 一致。
