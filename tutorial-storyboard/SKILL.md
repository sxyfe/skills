---
name: tutorial-storyboard
description: >
  Turns an approved tutorial voiceover script into work/timeline.json with five track types
  (host, screen, broll, gfx, sub) cut on sentence boundaries. Use when ai-host-tutorial reaches
  the storyboard stage, or the user says 五轨分镜、口播分镜、timeline.json、/tutorial-storyboard.
  Does not call APIs, record the screen, or render video.
disable-model-invocation: true
---

# 教程分镜

输入：已认稿的 `inputs/script.md`，以及 `work/job-state.json` 里的 `aspect`。  
输出：`work/timeline.json`。  
禁止回读主编排 skill。禁止生成视频。

## 步骤

1. 读脚本。按句切，不要按段落切成超长镜。单镜默认 2–8 秒。
2. 每句只标一个主 `type`：
   - 主持人面对镜头说话 → `host`
   - 必须看见真实界面（终端、网页、App）→ `screen`
   - 隐喻、情绪、3D/插画空镜 → `broll`
   - 键帽、箭头、技巧条、吉祥物 → `gfx`（可叠在上一镜的时间上，用相同起止或写进 `overlay`）
   - 只烧字幕、画面沿用上一镜 → `sub`，或写在该镜 `overlay`
3. `vo_text` 用口播原句，不要第三人称转述。
4. `visual` 写构图：口播窗位置、录屏占满还是嵌底板、空镜几个字的画面提示。
5. `screen` 镜写清要录什么操作，文件名建议 `sXX-短名.mp4` 或 `.png`，放入 `screen_file`。
6. `broll` 镜写 `broll_prompt`：主体、动作、时长 4–8 秒、不要出现可读 UI 文字。
7. 镜头 `id` 为 `s01` `s02`… 按时间排序，`end_s` 等于下一镜 `start_s`。最后一镜 `end_s` 写入根级 `duration_s`。
8. 更新 `job-state.json`：`stage=storyboard`，写完文件后仍保持 `gates.storyboard=pending`，等人认分镜。

## 切镜规则

- 证明步骤（点哪里、输入什么）必须 `screen`。空镜不能代替证据。
- 开场 3 秒内给钩子：要么口播窗，要么一句硬字幕。
- 同角色、同房间的口播窗保持同一构图描述，方便后面锁脸。
- 不要写「配图建议」这种说明书句子；`visual` 只写剪映里要摆的东西。

## timeline.json 形状

```json
{
  "version": 1,
  "aspect": "3:4",
  "duration_s": 0,
  "shots": [
    {
      "id": "s01",
      "start_s": 0,
      "end_s": 3.5,
      "type": "host",
      "vo_text": "",
      "visual": "",
      "overlay": "",
      "asset": null,
      "screen_file": null,
      "broll_prompt": null
    }
  ]
}
```

写完后把分镜表用 markdown 表格打给用户：id、时段、type、口播一句、画面一句。等人说「分镜过了」再交给主编排往下走。
