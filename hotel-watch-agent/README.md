# hotel-watch-agent

RollingGo **全球酒店价格监控** Skill：分步配置监控任务 → 预估 API → 用户确认 → 查价 → 条件触发告警（售罄回补 / 降价 / 组合触发）→ 携程·去哪儿·RollingGo 三链输出。适配 **Cursor、Claude Code、Codex、OpenClaw** 等支持 Skills 协议的 Agent 工具。

[中文](#中文) · [English](#english)

---

## 中文

### 功能

- **全球酒店**：任意国家/城市/地标，RollingGo `searchHotels` + `getHotelDetail`
- **分步访谈**：地点、酒店清单（≤10）、入住日、预算、房型、通知阈值
- **A/B 双层预算**（`budgetTiers`）：如公共温泉 ≤700 / 传统旅馆+二食 ≤800
- **单点触发**：绝对价、降幅金额/比例、售罄回补、含二食 plan
- **组合触发**（`compositeTriggers`）：跨晚凑齐不同酒店、单晚跨价等
- **单酒店特例**（`hotelOverrides`）：指定日期目标价、售罄高优先级
- **预估 → 确认 → 执行**：预估 **>100 次** API 须 `--confirm`
- **外部 cron + Agent**：脚本跑查价，有触发再唤 Agent 格式化三链告警
- **静默模式**：`silentUnlessTriggered=true` 时无触发只更新 JSON

### 典型用例

| 场景 | 示例说法 |
|------|----------|
| 日本温泉盯价 | 「帮我监控青森这几家温泉，10 月入住，700 以内有房或降价通知我」 |
| A/B 双层预算 | 「公共温泉 700、传统旅馆含二食 800，组合触发跨晚凑齐」 |
| 定时监控 | 「每天查一次这几家酒店，有触发再发三链告警」 |

### 在 Agent 中安装使用

本 Skill 可在 **Cursor、Claude Code、Codex、OpenClaw** 等支持 Skills 协议的 Agent 中使用。整体流程：**申请 Key → 安装 Skill → 配置 `.env` → 自检 → 分步配置监控 → 查价与告警**。

#### 前置条件

| 项 | 要求 |
|----|------|
| Python | 3.8 及以上（终端可执行 `python3`） |
| Agent | 支持 Skills 协议（能加载 `SKILL.md`） |
| RollingGo Key | 在 [rollinggo.store](https://rollinggo.store/) 申请的**酒店 MCP** Key（格式 `mcp_...`） |
| 网络 | 可访问 `mcp.rollinggo.cn` |

#### 第一步：申请 RollingGo API Key

1. 打开 **[rollinggo.store](https://rollinggo.store/)** 注册账号（文档见 [rollinggo.store/docs](https://rollinggo.store/docs)）
2. 申请 **酒店 MCP** API Key（以 `mcp_` 开头）
3. 妥善保存 Key，**勿公开分享**或提交到 Git 仓库

Key 用于调用 RollingGo 酒店查价接口；本 Skill 通过 Python 脚本查价，Key 写入 Skill 目录下的 `.env` 即可（见第三步）。

#### 第二步：安装 Skill

**方式 A — skills.sh（推荐，自动适配 Agent）**

```bash
npx skills add sxyfe/skills@hotel-watch-agent -g -y
```

安装后可在 [skills.sh/sxyfe/skills](https://skills.sh/sxyfe/skills) 查看说明。

**方式 B — 手动安装（链接或复制目录）**

将 `hotel-watch-agent` 整个文件夹放到所用 Agent 的 Skills 目录：

| Agent | 常见 Skills 目录 |
|-------|------------------|
| Cursor | `~/.cursor/skills/hotel-watch-agent` |
| Claude Code | 项目内 `.claude/skills/hotel-watch-agent`，或全局 `~/.claude/skills/` |
| 其他 Agent | 查阅该工具文档中的 Skills / 技能目录路径 |

```bash
# 示例：克隆后 symlink 到 Cursor
git clone https://github.com/sxyfe/skills.git
ln -s "$(pwd)/skills/skills/hotel-watch-agent" ~/.cursor/skills/hotel-watch-agent
```

**方式 C — 仅克隆源码**

```bash
git clone https://github.com/sxyfe/skills.git
cd skills/skills/hotel-watch-agent
```

安装完成后，**新开一轮 Agent 对话**或重启 Agent，以便加载 `SKILL.md`。

#### 第三步：配置 API Key

在 **Skill 根目录**（含 `SKILL.md` 的目录）执行：

```bash
cd skills/hotel-watch-agent   # 或你的实际安装路径
cp .env.example .env
```

编辑 `.env`，填入申请的 Key：

```bash
ROLLINGGO_API_KEY=mcp_你的密钥
```

也可在终端临时导出：

```bash
export ROLLINGGO_API_KEY=mcp_你的密钥
```

**可选 — MCP 配置**：若 Agent 同时支持 MCP，可参考 `templates/mcp.json.example` 配置 **RollingGo-Hotel** 服务。本 Skill 主流程走 Python 脚本，**优先读取 `.env`**，MCP 为可选增强。

#### 第四步：连通性自检

仍在 Skill 根目录：

```bash
python3 scripts/check_rollinggo_hotel.py
```

输出成功即表示 Key 有效、酒店 MCP 可达。

#### 第五步：在 Agent 对话中使用

安装与配置完成后，在 Agent 里用自然语言描述监控需求，例如：

- 「帮我监控东京这几家酒店，12 月 24–26 入住，1500 以内降价通知我」
- 「用 hotel-watch-agent 配置日本温泉 A/B 双层预算监控」
- 「生成 cron 定时任务，每天查一次，有触发再告警」

Agent 会按 `SKILL.md` 自动：分步访谈或加载预设 → 预估 API 次数 → 请你确认 → 执行查价 → 更新 state → 有触发时输出三链告警。

**首次建议**：可让 Agent「先跑连通性自检，再用全球通用预设创建一份 watch-config」，确认环境无误后再配置正式监控。

### 快速开始（命令行）

**要求**：Python 3.8+，RollingGo 酒店 MCP Key

1. **申请 Key**：[rollinggo.store](https://rollinggo.store/)（格式 `mcp_...`）

2. **配置**：

```bash
cd skills/hotel-watch-agent
cp .env.example .env
# 编辑 .env：ROLLINGGO_API_KEY=mcp_...
```

3. **自检**：

```bash
python3 scripts/check_rollinggo_hotel.py
```

4. **最小成功路径**（创建配置 → 预估 → 执行一轮）：

```bash
# 交互式创建（可用 --preset generic-worldwide 预填部分字段）
python3 scripts/init_watch_config.py --preset generic-worldwide -o ./output

python3 scripts/estimate_watch.py --config ./output/my-watch-config.json --json

python3 scripts/run_watch_round.py \
  --config ./output/my-watch-config.json \
  --state ./output/my-hotel-watch.json \
  --confirm
```

5. **生成定时 prompt**（外部 cron + Agent）：

```bash
python3 scripts/render_loop_prompt.py \
  --config ./output/my-watch-config.json \
  --mode both \
  -o ./output
# 产出：my-loop-prompt.txt、my-cron-prompt.txt
```

### 工作流概览

```
访谈/预设 → watch-config.json
              ↓
        estimate_watch（>100 次须用户确认）
              ↓
        run_watch_round（查价 + 写 state）
              ↓
     单点 triggers + compositeTriggers
              ↓
   cron：有触发 → Agent 格式化三链告警
```

### 配置文件说明

| 文件 | 用途 |
|------|------|
| `{slug}-watch-config.json` | 监控参数（只读，含 watchlist / dates / triggers） |
| `{slug}-hotel-watch.json` | 运行时 state（baseline / lastSnapshot / alertsSent） |
| `{slug}-loop-prompt.txt` | Agent 每轮指令 |
| `{slug}-cron-prompt.txt` | crontab 安装说明 |

示例配置见 `templates/watch-config.example.aomori.json`、`templates/watch-config.example.hakodate.json`。

### 失败态

| 现象 | 说明 |
|------|------|
| 无 Key / 自检失败 | 前往 [rollinggo.store](https://rollinggo.store/) 申请并配置 `.env` |
| MCP / API 调用失败 | 查价服务异常，检查 Key 与网络 |
| 预估 >100 次未确认 | 须用户明确确认后再 `--confirm` 执行 |
| 无触发且静默模式 | 正常；state 已更新，无需告警 |

### 脚本一览

| 脚本 | 作用 |
|------|------|
| `check_rollinggo_hotel.py` | 酒店 MCP 连通性 |
| `init_watch_config.py` | 分步 CLI + 预设 |
| `estimate_watch.py` | API 预估（不查价） |
| `run_watch_round.py` | **一轮监控闭环** |
| `render_loop_prompt.py` | loop / cron / 多任务合并 prompt |
| `extract_booking_links.py` | 携程 / 去哪儿 / RollingGo 三链 |
| `evaluate_triggers.py` | 离线单点触发测试 |

### 硬约束与反滥用

- 单次 watchlist **≤ 10 家**酒店
- 每入住日默认查 **1 晚**（非连住）
- 定时间隔建议 **≥12h**，推荐 24h
- **禁止**：高频刷接口、公开共享 Key、未经确认的超阈值批量查价

### RollingGo MCP（可选）

若 Agent 支持 MCP，可参考 `templates/mcp.json.example` 配置 **RollingGo-Hotel** 服务。Python 脚本优先读取 `.env` 中的 `ROLLINGGO_API_KEY`。

| 工具 | 用途 |
|------|------|
| `searchHotels` | 区域 + 标签 + 预算广度扫描 |
| `getHotelDetail` | 单酒店房型 / plan / 价格精查 |
| `getHotelSearchTags` | 标签参考 / 自检 |

完整安装步骤见上文 **[在 Agent 中安装使用](#在-agent-中安装使用)**。

### License

MIT

---

## English

### Features

- **Global hotels**: any country / city / POI via RollingGo `searchHotels` + `getHotelDetail`
- **Step-by-step setup**: place, watchlist (≤10), dates, budget, room prefs, alert thresholds
- **Dual budget tiers** (`budgetTiers`), composite triggers, per-hotel overrides
- **Estimate → confirm → run**: >100 API calls require `--confirm`
- **External cron + Agent**: script runs queries; Agent formats tri-link alerts on trigger
- Works with **Cursor, Claude Code, Codex, OpenClaw**, and other Skills-compatible agents

### Install & Use in an Agent

1. **Prerequisites**: Python 3.8+, Skills-compatible agent, RollingGo **Hotel** MCP Key from [rollinggo.store](https://rollinggo.store/) (`mcp_...`)
2. **Install**: `npx skills add sxyfe/skills@hotel-watch-agent -g -y` — or symlink this folder into your agent's skills directory
3. **Configure**: In the skill root, `cp .env.example .env` and set `ROLLINGGO_API_KEY`
4. **Verify**: `python3 scripts/check_rollinggo_hotel.py`
5. **Use**: Ask in natural language, e.g. *"Watch these Tokyo hotels for Dec 24–26, alert me if price drops below 1500 CNY"*

See the Chinese section **[在 Agent 中安装使用](#在-agent-中安装使用)** for full steps.

### Quick Start (CLI)

1. Get Key at [rollinggo.store](https://rollinggo.store/)
2. `cp .env.example .env` → set `ROLLINGGO_API_KEY`
3. `python3 scripts/check_rollinggo_hotel.py`
4. `init_watch_config.py` → `estimate_watch.py` → `run_watch_round.py --confirm`
5. Optional: `render_loop_prompt.py --mode both` for cron setup

### License

MIT
