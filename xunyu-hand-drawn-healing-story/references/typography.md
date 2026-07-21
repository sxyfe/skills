# 字体规范（默认写死 · 无参考图文件）

本 skill **不附带**任何对标截图 / 参考 PNG。只描述目标体感与字体文件路径。

流水线位置：旁白 PNG / 各引擎 `@font-face` → [`pipeline.md`](pipeline.md) §4。 
可调键：`typography.*` → [`defaults.md`](defaults.md)。

## 目标体感

1. **圆润手写印刷体**：笔画末端略圆、字重均匀中等、整齐可读、手帐感——不是宋体印刷、黑体标题、狂草书法、二次元可爱糊字。 
2. **字色**：`#222222`；可选极淡白描边（2px）防糊。 
3. **行距宽松**：`line-height ≈ 1.7`；字距约 `0.04em`。 
4. **位置**：水平居中，距顶约 **6.5%** 画高；每镜 1–2 行，单行 ≤18 字。 
5. **图内标签**：最多 2 字；长旁白一律后期叠，不烧进图。

## 内置字体

| 文件 | 说明 |
|---|---|
| `assets/fonts/ZCOOLKuaiLe-Regular.ttf` | 默认：站酷快乐体（Google Fonts / **OFL**） |
| `assets/fonts/RoundedHandwrite.ttf` | 指向同上的稳定别名（symlink） |
| `assets/fonts/OFL-ZCOOLKuaiLe.txt` | 许可证全文 |

`defaults.yaml` → `typography.font_file` 指向上述 ttf。

若你有更贴近个人对标的手写体，把 `.ttf` / `.otf` 放到 `assets/fonts/` 并改 `font_file`（确认授权后再用于公开分发）。

## 系统回退（仅应急）

`Kaiti.ttc` → `Songti.ttc`。交付前应换回手写体。

## 实现

- **脚本合成**：`scripts/make_captions.py` 按 `font_candidates` 加载。 
- **HTML / Remotion / HyperFrames**：`@font-face` 指向同一 ttf。 
- 多行用 `\n` 手动断行。

## 质检

- [ ] 观感是圆润手写，而非宋/黑印刷 
- [ ] 行距透气；手机竖屏可读 
- [ ] 不压住人头顶；无长旁白烧进母图
