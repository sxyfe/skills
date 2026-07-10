# flight-monitor-agent

RollingGo **航班实时查价** Skill：自然语言 → 精简/全量穷举查价 → 暖色分页 HTML 报告。适配 **Cursor、Claude Code、Codex、OpenClaw** 等支持 Skills 协议的 Agent 工具。

[中文](#中文) · [English](#english)

---

## 中文

### 功能

- 自然语言解析为 SearchIntent（国庆/国庆前后、多国、预算、开口程）
- **精简模式**（`--mode smart`）：各国热门城市子集，快速扫价（日常推荐）
- **全量穷举**（`--mode exhaustive`）：覆盖全部配置城市，API 成本高，须确认
- 往返联票 + 开口程（A→B + C→D，A/D 须在出发地集合内）
- 暖色 HTML 报告：侧栏筛选、Chart.js 图表、排序、筛选后全量分页与页码跳转
- **预估 → 确认 → 执行**：预估 **>500 次** API 时 `run_search.py` 须加 `--confirm`

### 典型用例

| 场景 | 示例查询 |
|------|----------|
| 国庆东南亚多国穷举 | `北京出发泰国菲律宾国庆特价2500以内` |
| 京津开口程 | `国庆前后京津出发，去马尼拉回棉兰，开口程` |
| 快速扫价 | `上海东京往返10月1日，精简模式` |

### 在 Agent 中安装使用

本 Skill 可在 **Cursor、Claude Code、Codex、OpenClaw** 等支持 Skills 协议的 Agent 中使用。整体流程：**申请 Key → 安装 Skill → 配置 `.env` → 自检 → 自然语言查价**。

#### 前置条件

| 项 | 要求 |
|----|------|
| Python | 3.8 及以上（终端可执行 `python3`） |
| Agent | 支持 Skills 协议（能加载 `SKILL.md`） |
| RollingGo Key | 在 [rollinggo.store](https://rollinggo.store/) 申请的航班 MCP Key（格式 `mcp_...`） |
| 网络 | 可访问 `mcp.rollinggo.cn` |

#### 第一步：申请 RollingGo API Key

1. 打开 **[rollinggo.store](https://rollinggo.store/)** 注册账号
2. 申请 **航班 MCP** API Key（以 `mcp_` 开头）
3. 妥善保存 Key，**勿公开分享**或提交到 Git 仓库

Key 用于调用 RollingGo 航班查价接口；本 Skill 通过 Python 脚本查价，Key 写入 Skill 目录下的 `.env` 即可（见第三步）。

#### 第二步：安装 Skill

**方式 A — skills.sh（推荐，自动适配 Agent）**

```bash
npx skills add sxyfe/skills@flight-monitor-agent -g -y
```

安装后可在 [skills.sh/sxyfe/skills](https://skills.sh/sxyfe/skills) 查看说明。`-g` 为全局安装，具体目录由所用 Agent 决定。

**方式 B — 手动安装（链接或复制目录）**

将 `flight-monitor-agent` 整个文件夹放到所用 Agent 的 Skills 目录：

| Agent | 常见 Skills 目录 |
|-------|------------------|
| Cursor | `~/.cursor/skills/flight-monitor-agent` |
| Claude Code | 项目内 `.claude/skills/flight-monitor-agent`，或全局 `~/.claude/skills/` |
| 其他 Agent | 查阅该工具文档中的 Skills / 技能目录路径 |

```bash
# 示例：克隆后 symlink 到 Cursor
git clone https://github.com/sxyfe/skills.git
ln -s "$(pwd)/skills/skills/flight-monitor-agent" ~/.cursor/skills/flight-monitor-agent
```

**方式 C — 仅克隆源码（开发 / 自行管理）**

```bash
git clone https://github.com/sxyfe/skills.git
cd skills/skills/flight-monitor-agent
```

安装完成后，**新开一轮 Agent 对话**或重启 Agent，以便加载 `SKILL.md`。

#### 第三步：配置 API Key

在 **Skill 根目录**（含 `SKILL.md` 的目录）执行：

```bash
cd skills/flight-monitor-agent   # 或你的实际安装路径
cp .env.example .env
```

编辑 `.env`，填入申请的 Key：

```bash
ROLLINGGO_API_KEY=mcp_你的密钥
ROLLINGGO_BASE_URL=https://mcp.rollinggo.cn
```

也可在终端临时导出（不写文件）：

```bash
export ROLLINGGO_API_KEY=mcp_你的密钥
```

**可选 — MCP 配置**：若 Agent 同时支持 MCP 且需单次补查，可参考 `templates/mcp.json.example` 配置 **RollingGo-Flight** 服务。本 Skill 主流程走 Python 脚本，**优先读取 `.env`**，MCP 为可选增强。

#### 第四步：连通性自检

仍在 Skill 根目录：

```bash
python3 scripts/check_rollinggo.py
```

输出成功即表示 Key 有效、航班查价 API 可达。失败时请检查 Key 是否正确、网络是否正常。

#### 第五步：在 Agent 对话中使用

安装与配置完成后，**无需记命令**，在 Agent 里用自然语言描述需求即可，例如：

- 「帮我查北京出发，泰国菲律宾国庆特价 2500 以内」
- 「京津开口程，国庆前后，去马尼拉、回棉兰」
- 「用精简模式扫一下上海东京 10 月 1 日往返」

Agent 会按 `SKILL.md` 自动：解析意图 → 展示精简/全量穷举预估 → 请你选模式 → 实时查价 → 生成 HTML 报告并告知路径。

**首次建议**：可让 Agent「按最小成功路径试跑一遍」，确认环境无误后再做大规模穷举。

### 快速开始（命令行）

**要求**：Python 3.8+，RollingGo API Key

1. **申请 Key**：[rollinggo.store](https://rollinggo.store/)（格式 `mcp_...`）

2. **配置**：

```bash
cd skills/flight-monitor-agent
cp .env.example .env
# 编辑 .env：ROLLINGGO_API_KEY=mcp_...
```

3. **自检**：

```bash
python3 scripts/check_rollinggo.py
```

4. **最小成功路径**（首次约 2 分钟出报告）：

```bash
python3 scripts/parse_nl_intent.py \
  -q "北京曼谷往返10月1日2500以内" \
  --rules-only \
  -o output/intent.json

python3 scripts/run_search.py --intent output/intent.json --mode smart \
  --output output/search_result.json

python3 scripts/generate_flight_report.py --input output/search_result.json
# 报告路径见 stdout 的 report_path（默认 output/reports/<timestamp>/report.html）
```

5. **完整工作流**（含模式选择与预估）：

```bash
# 解析意图（含精简/全量 API 预估）
python3 scripts/parse_nl_intent.py \
  -q "北京出发泰国菲律宾国庆特价2500以内" \
  --rules-only \
  -o output/intent.json

# 仅预估
python3 scripts/run_search.py --intent output/intent.json --mode smart --estimate-only

# 精简模式查价
python3 scripts/run_search.py --intent output/intent.json --mode smart \
  --output output/search_result.json

# 全量穷举（预估 >500 次须 --confirm）
python3 scripts/run_search.py --intent output/intent.json --mode exhaustive --confirm \
  --output output/search_result.json

python3 scripts/generate_flight_report.py --input output/search_result.json
```

### 工作流概览

```
自然语言 → parse_nl_intent（预估 smart / exhaustive 次数）
              ↓
        用户选择模式并确认（>500 次须明确确认）
              ↓
        run_search.py → search_result.json
              ↓
        generate_flight_report.py → output/reports/<timestamp>/report.html
```

### 精简模式 vs 全量穷举

| | 精简模式 | 全量穷举 |
|---|----------|----------|
| 命令行 | `--mode smart` | `--mode exhaustive` |
| 目的地 | 各国热门城市 | 全量配置城市 |
| API 次数 | 较少（日常） | 可能数千 |
| 确认阈值 | 一般无需 | **>500 次须 `--confirm`** |

**Agent MUST**：向用户展示两种模式预估次数与耗时，让用户二选一；未确认时拒绝超阈值执行。

### 失败态

| 现象 | 说明 |
|------|------|
| 无 Key / 自检失败 | 前往 [rollinggo.store](https://rollinggo.store/) 申请并配置 `.env` |
| API `success: false` | 查价服务异常，非「无票」 |
| 预估 >500 次未确认 | 须用户明确确认后再执行全量穷举 |

### 脚本一览

| 脚本 | 作用 |
|------|------|
| `check_rollinggo.py` | RollingGo 连通性 |
| `parse_nl_intent.py` | 自然语言 → SearchIntent + 规则/预估 |
| `run_search.py` | 实时查价（smart / exhaustive） |
| `generate_flight_report.py` | JSON → 分页 HTML 报告 |
| `flight_search_engine.py` | 查价引擎核心 |
| `holiday_windows.py` | 国庆等日期窗 |

### 硬约束与反滥用

本工具供个人与 Agent **合理**机票查价。RollingGo API Key 有使用边界，**请勿**：

- 高频自动化刷接口
- 将 Key 公开分享或用于多租户公共服务
- 绕过确认机制批量全量穷举

### RollingGo MCP（可选）

若 Agent 支持 MCP，可参考 `templates/mcp.json.example` 配置 **RollingGo-Flight** 服务。Python 脚本优先读取 `.env` 中的 `ROLLINGGO_API_KEY`。完整安装步骤见上文 **[在 Agent 中安装使用](#在-agent-中安装使用)**。

### License

MIT — 见 [LICENSE](LICENSE)

---

## English

### Features

- Natural language → SearchIntent (holidays, multi-country, budget, open-jaw)
- **Compact scan** (`--mode smart`): hot-city subset for quick checks
- **Full sweep** (`--mode exhaustive`): all configured cities (high cost, confirmation required)
- Round-trip + open-jaw (outbound A→B, return C→D; A and D in origin set)
- Warm editorial HTML report: filters, Chart.js, sort, paginated results
- **Estimate → confirm → run**: >500 API calls require `--confirm`
- Works with **Cursor, Claude Code, Codex, OpenClaw**, and other Skills-compatible agents

### Install & Use in an Agent

1. **Prerequisites**: Python 3.8+, Skills-compatible agent, RollingGo flight MCP Key from [rollinggo.store](https://rollinggo.store/) (`mcp_...`)
2. **Install**: `npx skills add sxyfe/skills@flight-monitor-agent -g -y` — or symlink this folder into your agent's skills directory
3. **Configure**: In the skill root, `cp .env.example .env` and set `ROLLINGGO_API_KEY`
4. **Verify**: `python3 scripts/check_rollinggo.py`
5. **Use**: Ask in natural language, e.g. *"Find Beijing–Bangkok round trips under 2500 for National Day"*

See the Chinese section **[在 Agent 中安装使用](#在-agent-中安装使用)** for full steps (Key application, per-agent paths, MCP optional setup).

### Quick Start (CLI)

### License

MIT — see [LICENSE](LICENSE)
