# skills

RollingGo 旅行查价 Agent Skills 合集，可通过 [skills.sh](https://skills.sh) 安装到 Cursor、Claude Code、Codex 等 40+ Agent。

[![skills.sh](https://img.shields.io/badge/skills.sh-sxyfe%2Fskills-blue)](https://skills.sh/sxyfe/skills)

## Skill 目录

| Skill | 说明 | MCP 服务 | 安装 |
| --- | --- | --- | --- |
| [flight-monitor-agent](flight-monitor-agent/) | 航班实时查价、精简/全量穷举、暖色 HTML 分页报告 | RollingGo-Flight | `npx skills add sxyfe/skills@flight-monitor-agent -g -y` |
| [hotel-watch-agent](hotel-watch-agent/) | 全球酒店价格监控、A/B 预算、组合触发、cron+Agent 定时告警 | RollingGo-Hotel | `npx skills add sxyfe/skills@hotel-watch-agent -g -y` |

### 两者对比

| | flight-monitor-agent | hotel-watch-agent |
|---|---------------------|-------------------|
| 典型场景 | 「帮我查国庆东南亚特价」 | 「盯着这几家酒店，降价/有房通知我」 |
| 输出 | 一次性 HTML 报告 | 持久 state JSON + 条件告警 |
| API 确认阈值 | >500 次 | >100 次 |
| 源码位置 | 本仓库 `flight-monitor-agent/` | 本仓库 `hotel-watch-agent/` |

共用 [RollingGo API Key](https://rollinggo.store/)（`mcp_...`），Flight / Hotel 分别配置 MCP。

## 安装

```bash
# 航班查价
npx skills add sxyfe/skills@flight-monitor-agent -g -y

# 酒店监控
npx skills add sxyfe/skills@hotel-watch-agent -g -y

# 仅 Cursor
npx skills add sxyfe/skills@flight-monitor-agent -g -y -a cursor
```

### 本地开发

两个 Skill 源码均在本仓库根目录。本地调试时，可将目录链接到所用 Agent 的 Skills 路径：

```bash
# 在仓库根目录执行；将 REPO_ROOT 替换为你的克隆路径
REPO_ROOT="$(pwd)"

# Cursor
ln -s "$REPO_ROOT/flight-monitor-agent" ~/.cursor/skills/flight-monitor-agent
ln -s "$REPO_ROOT/hotel-watch-agent" ~/.cursor/skills/hotel-watch-agent

# Claude Code（项目级示例）
mkdir -p .claude/skills
ln -s "$REPO_ROOT/flight-monitor-agent" .claude/skills/flight-monitor-agent
```

修改源码后，**新开 Agent 对话**或重启 Agent 以重新加载 `SKILL.md`。

## 仓库结构

```
skills/
├── README.md
├── flight-monitor-agent/     # 航班查价（源码）
│   ├── SKILL.md
│   ├── README.md
│   ├── scripts/
│   └── templates/
└── hotel-watch-agent/        # 酒店监控
    ├── SKILL.md
    ├── README.md
    ├── scripts/
    ├── templates/
    └── references/
```

## 要求

- Python 3.8+
- [RollingGo API Key](https://rollinggo.store/)

## License

各 Skill 目录内 LICENSE 为准（均为 MIT）。
