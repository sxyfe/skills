# skills

Agent Skills 合集，可通过 [skills.sh](https://skills.sh) 安装到 Cursor、Claude Code、Codex 等 40+ Agent。

[![skills.sh](https://img.shields.io/badge/skills.sh-sxyfe%2Fskills-blue)](https://skills.sh/sxyfe/skills)

## 安装

```bash
# 安装 flight-monitor-agent（全局，Cursor / Claude Code 等）
npx skills add sxyfe/skills@flight-monitor-agent -g -y

# 仅安装到 Cursor
npx skills add sxyfe/skills@flight-monitor-agent -g -y -a cursor
```

## Skill 目录

| Skill | 说明 | 安装 |
| --- | --- | --- |
| [flight-monitor-agent](skills/flight-monitor-agent/) | RollingGo 航班实时查价、精简/全量穷举、暖色 HTML 分页报告 | `npx skills add sxyfe/skills@flight-monitor-agent -g -y` |

## 仓库结构

```
skills/
├── README.md
└── skills/
    └── flight-monitor-agent/
        ├── SKILL.md
        ├── README.md
        ├── scripts/
        └── templates/
```

## 要求

- Python 3.8+
- [RollingGo API Key](https://rollinggo.store/)（flight-monitor-agent）

## License

各 Skill 目录内 LICENSE 为准（flight-monitor-agent 为 MIT）。
