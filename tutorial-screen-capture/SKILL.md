---
name: tutorial-screen-capture
description: >
  Builds a screen-recording shot list from timeline.json screen shots and waits for the user
  to drop real captures into inputs/screen/. Use when ai-host-tutorial needs operation footage,
  or the user says 录屏清单、截图镜头单、/tutorial-screen-capture. Never synthesizes IDE or
  website UIs. Never operates the user's logged-in browser session.
disable-model-invocation: true
---

# 录屏镜头单

输入：`work/timeline.json` 里 `type=screen` 的镜头。  
输出：`work/screen-shotlist.md`，并更新 `job-state.json` 的 `gates.screen`。  
禁止回读主编排 skill。禁止用模型生成界面。禁止去碰浏览器登录态。

## 步骤

1. 列出全部 `screen` 镜头。没有就写「本片无录屏镜」，`gates.screen=received`，结束。
2. 写成 `work/screen-shotlist.md`，每个镜头包含：
   - 镜头 id 与时段
   - 要打开的软件/网址（只写名称，不写密码）
   - 操作步骤（点哪里、输入什么、停在哪一帧）
   - 建议文件名（与 `screen_file` 一致）
   - 画幅：跟 `timeline.aspect`；录的时候尽量高清，竖屏成片可后期裁
   - 光标：配音说到「看这里」时，光标要停在那个控件上
3. `gates.screen = waiting_user`。`stage = screen`。
4. 把清单给用户。明确：把文件放到 `inputs/screen/`，文件名对上表。
5. 用户说放好了，或目录里出现对应文件：核对每个 `screen_file` 是否存在。缺的列出来再停。
6. 收齐后把实到文件名写入 `tracks.screen.received`，`gates.screen = received`。

## 拍摄注意事项（写进清单顶部）

- 关掉通知、隐私窗口、密钥、真实手机号。
- 终端字体放大，避免竖屏看不清。
- 能用一段连续录屏覆盖多镜就在清单里注明切点秒数，减少反复开录。
- 静态页可以用 png；有光标移动用 mp4。

## screen-shotlist.md 模板

```markdown
# 录屏镜头单

画幅：3:4
放置目录：inputs/screen/

| id | 时段 | 文件名 | 操作 | 状态 |
|---|---|---|---|---|
| s04 | 12.0–18.0 | s04-filter.mp4 | 打开目标页，光标点筛选 | 待收 |
```
