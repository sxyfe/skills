# templates/ · 最小可运行骨架

本目录**不含** `node_modules`、示例 PNG、成片 mp4。复制后自行 `npm install` 并放入素材。

| 子目录 | 用途 |
|---|---|
| `html/` | 浏览器预览（零构建） |
| `remotion/` | Remotion Studio / render |
| `hyperframes/` | HyperFrames Studio / render |
| （默认成片） | 用 skill 根目录 `scripts/`，无需本 templates |

完整带素材的样本（可选复制，排除体积大文件）：

```bash
SRC="./samples/episode-01-four-engines"
# 例：rsync -a --exclude node_modules --exclude out "$SRC/02-remotion/" ./02-remotion/
```

详见 `references/engines.md`。
