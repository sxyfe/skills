# 文稿提取路由

不要新装 YouTube / B 站字幕 skill。本机已经有两个，由 `cli.py transcript` 调用。

| 来源 | 调用的 skill | 做什么 |
|---|---|---|
| YouTube | `baoyu-youtube-transcript` | 拉平台字幕（中文优先，没有再英文）。失败则交给下一行 |
| B 站 / YouTube 兜底 | `video-subtitle-parser`，失败再用 yt-dlp 字幕轨 | 平台字幕优先 |
| 本地视频 | 本 skill 脚本 | 先抽内嵌字幕轨；没有再 `mlx-whisper` |

## 命令

```bash
python3 {baseDir}/scripts/cli.py transcript --url URL --out-dir DIR
python3 {baseDir}/scripts/cli.py transcript --video /path/to.mp4 --out-dir DIR
```

成功时 stdout 是 JSON，里面有 `transcript` 路径。金句只从该文件出，并保留可回查的原句。

## 失败时

- YouTube / B 站没字幕：先停，让用户换一条有字幕的访谈，或补本地视频
- 本地视频没内嵌字幕且没装 `mlx-whisper`：告诉用户  
  `python3 -m pip install mlx-whisper`（Apple Silicon）
- 不绕过登录、付费墙、加密

## 不要装的

生态里还有很多 `youtube-transcript`、`bilibili-transcript`、`whisper-transcription`。功能重复，且本机这两套已经覆盖三条来源。
