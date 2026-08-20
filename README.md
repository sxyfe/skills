# skills

Agent Skills 合集，可通过 [skills.sh](https://skills.sh) 安装到 Cursor、Claude Code、Codex 等 40+ Agent。

[![skills.sh](https://img.shields.io/badge/skills.sh-sxyfe%2Fskills-blue)](https://skills.sh/sxyfe/skills)

## Skill 目录

| Skill | 说明 | 依赖 | 安装 |
| --- | --- | --- | --- |
| [ai-host-tutorial](ai-host-tutorial/) | AI 口播教程主编排：五轨交接（口播 / 真录屏 / 空镜 / 贴图 / 字幕），15 秒预览门禁，只出剪映时间轴 | Python 3；口播轨可选 MiniMax+HeyGen | `npx skills add sxyfe/skills@ai-host-tutorial -g -y` |
| [tutorial-storyboard](tutorial-storyboard/) | 口播稿 → `timeline.json` 五轨分镜 | 无 | `npx skills add sxyfe/skills@tutorial-storyboard -g -y` |
| [tutorial-screen-capture](tutorial-screen-capture/) | 按分镜出录屏清单，等人放入真实截图/录像 | 无 | `npx skills add sxyfe/skills@tutorial-screen-capture -g -y` |
| [ai-broll-lock](ai-broll-lock/) | 一张定妆图出 4–8 秒空镜，锁角色与场景 | 图生视频 API（用户自备） | `npx skills add sxyfe/skills@ai-broll-lock -g -y` |
| [tutorial-composite](tutorial-composite/) | 各轨素材 → 剪映/CapCut 图层时间轴清单 | 无 | `npx skills add sxyfe/skills@tutorial-composite -g -y` |
| [xhs-interview-cards](xhs-interview-cards/) | 真实公开访谈 → 金句笔记 + 花卷字幕截图条（本地生产，不自动发布） | ffmpeg + yt-dlp + Pillow | `npx skills add sxyfe/skills@xhs-interview-cards -g -y` |
| [xunyu-hand-drawn-healing-story](xunyu-hand-drawn-healing-story/) | 白色极简手绘竖屏短视频（主题通用）：一句话出片，默认 video-use，另支持 HTML / Remotion / Hyperframes | ffmpeg + Python；生图可选 | `npx skills add sxyfe/skills@xunyu-hand-drawn-healing-story -g -y` |
| [flight-monitor-agent](flight-monitor-agent/) | 航班实时查价、精简/全量穷举、暖色 HTML 分页报告 | RollingGo-Flight MCP | `npx skills add sxyfe/skills@flight-monitor-agent -g -y` |
| [hotel-watch-agent](hotel-watch-agent/) | 全球酒店价格监控、A/B 预算、组合触发、cron+Agent 定时告警 | RollingGo-Hotel MCP | `npx skills add sxyfe/skills@hotel-watch-agent -g -y` |

## 安装

```bash
# AI 口播教程五轨（建议五条一起装）
npx skills add sxyfe/skills@ai-host-tutorial -g -y
npx skills add sxyfe/skills@tutorial-storyboard -g -y
npx skills add sxyfe/skills@tutorial-screen-capture -g -y
npx skills add sxyfe/skills@ai-broll-lock -g -y
npx skills add sxyfe/skills@tutorial-composite -g -y

# 人物访谈截图
npx skills add sxyfe/skills@xhs-interview-cards -g -y

# 手绘竖屏短视频（通用）
npx skills add sxyfe/skills@xunyu-hand-drawn-healing-story -g -y

# 航班查价
npx skills add sxyfe/skills@flight-monitor-agent -g -y

# 酒店监控
npx skills add sxyfe/skills@hotel-watch-agent -g -y

# 仅 Cursor
npx skills add sxyfe/skills@xhs-interview-cards -g -y -a cursor
```

浏览：https://skills.sh/sxyfe/skills

### 本地开发

Skill 源码均在本仓库根目录。本地调试时，可将目录链接到所用 Agent 的 Skills 路径：

```bash
REPO_ROOT="$(pwd)"

# Cursor
ln -sfn "$REPO_ROOT/ai-host-tutorial" ~/.cursor/skills/ai-host-tutorial
ln -sfn "$REPO_ROOT/tutorial-storyboard" ~/.cursor/skills/tutorial-storyboard
ln -sfn "$REPO_ROOT/tutorial-screen-capture" ~/.cursor/skills/tutorial-screen-capture
ln -sfn "$REPO_ROOT/ai-broll-lock" ~/.cursor/skills/ai-broll-lock
ln -sfn "$REPO_ROOT/tutorial-composite" ~/.cursor/skills/tutorial-composite
ln -sfn "$REPO_ROOT/xhs-interview-cards" ~/.cursor/skills/xhs-interview-cards
ln -sfn "$REPO_ROOT/xunyu-hand-drawn-healing-story" ~/.cursor/skills/xunyu-hand-drawn-healing-story
ln -sfn "$REPO_ROOT/flight-monitor-agent" ~/.cursor/skills/flight-monitor-agent
ln -sfn "$REPO_ROOT/hotel-watch-agent" ~/.cursor/skills/hotel-watch-agent

# Claude Code（项目级示例）
mkdir -p .claude/skills
ln -sfn "$REPO_ROOT/xhs-interview-cards" .claude/skills/xhs-interview-cards
```

修改源码后，**新开 Agent 对话**或重启 Agent 以重新加载 `SKILL.md`。

## 仓库结构

```
skills/
├── README.md
├── ai-host-tutorial/                 # 口播教程主编排
├── tutorial-storyboard/
├── tutorial-screen-capture/
├── ai-broll-lock/
├── tutorial-composite/
├── xhs-interview-cards/              # 人物访谈截图
│   ├── SKILL.md
│   ├── README.md
│   ├── assets/
│   ├── scripts/
│   └── references/
├── xunyu-hand-drawn-healing-story/   # 白色极简手绘竖屏（通用）
│   ├── SKILL.md
│   ├── README.md
│   ├── assets/
│   ├── scripts/
│   ├── templates/
│   └── references/
├── flight-monitor-agent/             # 航班查价
└── hotel-watch-agent/                # 酒店监控
```

## 旅行类 Skill 说明

`flight-monitor-agent` 与 `hotel-watch-agent` 共用 [RollingGo API Key](https://rollinggo.store/)（`mcp_...`），Flight / Hotel 分别配置 MCP。

| | flight-monitor-agent | hotel-watch-agent |
|---|---------------------|-------------------|
| 典型场景 | 「帮我查国庆东南亚特价」 | 「盯着这几家酒店，降价/有房通知我」 |
| 输出 | 一次性 HTML 报告 | 持久 state JSON + 条件告警 |

## 要求

- Python 3.8+（多数 Skill）
- 口播教程五轨：主编排用 Python 初始化 state；真录屏由用户提供；口播/空镜 API 自备账号。禁止用模型生成可读 IDE
- 人物访谈截图：本机 `ffmpeg`、`yt-dlp`、Pillow；中文字体
- 手绘视频：本机 `ffmpeg`；完整生图需配置可选 API Key
- 旅行监控：RollingGo API Key

## License

各 Skill 目录内 LICENSE 为准（均为 MIT）。
