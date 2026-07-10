---
name: flight-monitor-agent
description: >-
  机票实时查价 Skill：RollingGo 查价、精简/全量穷举、暖色 HTML 分页报告。
  用户说「查机票」「穷举搜索」「RollingGo 查价」「国庆特价」「开口程」「东南亚/日本/菲律宾机票」时使用。
  适配 Cursor、Claude Code、Codex、OpenClaw 等支持 Skills 协议的 Agent 工具。
---

# Flight Monitor Agent

自然语言 → **实时 RollingGo 查价** → 分页 HTML 报告（`output/reports/<timestamp>/report.html`）。

## 安装与配置（引导用户）

用户询问「怎么安装 / 怎么用 / 需要什么 Key」时，按以下顺序说明（适配 Cursor、Claude Code、Codex、OpenClaw 等 Skills 协议 Agent）：

### 前置条件

- **Python 3.8+**（终端可执行 `python3`）
- **RollingGo 航班 MCP Key**：在 [rollinggo.store](https://rollinggo.store/) 申请，格式 `mcp_...`
- 所用 Agent 已支持 Skills（能加载本目录 `SKILL.md`）

### 安装 Skill

**推荐（skills.sh）**：

```bash
npx skills add sxyfe/skills@flight-monitor-agent -g -y
```

**手动**：将本 Skill 目录链接或复制到 Agent 的 Skills 目录，例如 Cursor `~/.cursor/skills/flight-monitor-agent`、Claude Code `.claude/skills/flight-monitor-agent`。安装后新开对话或重启 Agent。

### 配置 Key

在 **Skill 根目录**（本文件所在目录）：

```bash
cp .env.example .env
# 编辑 .env：ROLLINGGO_API_KEY=mcp_...
python3 scripts/check_rollinggo.py
```

自检通过后再查价。**无 Key 时禁止调用 `run_search.py`**，须引导用户完成上述配置。

可选：Agent 若支持 MCP，可参考 `templates/mcp.json.example` 配置 RollingGo-Flight；脚本**优先读 `.env`**。

### 在 Agent 中使用

配置完成后，用户直接用自然语言描述查价需求即可（如「北京出发泰国菲律宾国庆特价2500以内」）。Agent 执行本 Skill 工作流：解析意图 → 展示精简/全量预估 → 用户选模式 → 查价 → 生成 HTML 报告。

## 最小成功路径（首次用户）

在 Skill 根目录依次执行，约 2 分钟可见第一份报告：

```bash
python3 scripts/check_rollinggo.py

python3 scripts/parse_nl_intent.py \
  -q "北京曼谷往返10月1日2500以内" \
  --rules-only \
  -o output/intent.json

python3 scripts/run_search.py --intent output/intent.json --mode smart \
  --output output/search_result.json

python3 scripts/generate_flight_report.py --input output/search_result.json
# 打开 stdout 中 report_path 指向的 report.html
```

## 前置条件（必读）

1. 已完成上文 **[安装与配置](#安装与配置引导用户)**：Skill 已安装、`.env` 已填 Key、`check_rollinggo.py` 已通过
2. 若用户尚未配置 Key → 引导前往 [rollinggo.store](https://rollinggo.store/) 申请并写入 `.env`，**不得**跳过直接查价

## 反滥用

本 Skill **不是**免费无限 API 的滥用工具。禁止：高频自动化刷接口、公开共享 Key、绕过确认机制批量穷举。大量查询前须让用户选择 **精简模式** 或明确 **--confirm**。

## 何时使用

- 用户要查多国特价、开口程、往返联票
- 用户提到国庆/国庆前后 + 出发地 + 预算
- 用户说「查机票」「穷举」「RollingGo 查价」

## 工作流

### 1. 解析意图

```bash
python3 scripts/parse_nl_intent.py \
  -q "国庆前后东南亚，京津出发，2500以内" \
  --rules-only \
  -o output/intent.json
```

输出含**精简模式**与**全量穷举**两种预估 API 次数与耗时（JSON 字段 `estimated_queries_smart`、`estimated_queries_exhaustive`）。

### 2. 模式选择与用户确认

| 模式 | 说明 | 命令行 `--mode` |
|------|------|-----------------|
| **精简模式** | 各国热门城市子集，适合快速扫价（推荐日常使用） | `smart` |
| **全量穷举** | 覆盖配置内全部城市，API 次数多、耗时长 | `exhaustive` |

**Agent MUST**：
1. 向用户展示两种模式的预估 API 次数与约计耗时（用中文说明，勿对用户说英文模式名）
2. 让用户在**精简模式**与**全量穷举**中二选一
3. 若选定模式预估 **>500 次** 且无用户明确确认 → **拒绝执行**

### 3. 实时查价

**禁止**读取历史 JSON 缓存（如 `exhaustive_results.json`）代替查价。

```bash
# 仅预估
python3 scripts/run_search.py --intent output/intent.json --mode smart --estimate-only

# 查价（精简模式）
python3 scripts/run_search.py --intent output/intent.json --mode smart \
  --output output/search_result.json

# 全量穷举：预估超 500 次时需 --confirm
python3 scripts/run_search.py --intent output/intent.json --mode exhaustive --confirm \
  --output output/search_result.json
```

### 4. 开口程规则

去程 **A→B**，返程 **C→D**：

| 端点 | 约束 |
|------|------|
| A、D | 必须在用户出发地集合内 |
| B、C | 任意目的地（可不同，实现开口） |

价格为两段单程最低价相加，`bookable: false`。

### 5. 生成 HTML 报告

```bash
python3 scripts/generate_flight_report.py \
  --input output/search_result.json
```

报告为暖色编辑风自包含 HTML，含：

- 侧栏筛选：行程类型、国家、目的地、出发地、价格区间与价格档位
- Chart.js 五图（随筛选联动）
- 表格排序 + **筛选后全量分页**（上一页/下一页、每页条数、页码跳转）
- 列：序号、类型、路线、日期、价格、可订、航班详情

### 6. 交付清单（中文）

- Key 与查价模式说明（精简 / 全量穷举）
- 预估/实际 API 次数
- 命中：往返 N / 开口程 M / 最低价
- 报告路径：`output/reports/<timestamp>/report.html`（见 `generate_flight_report.py` stdout 的 `report_path`）

## 失败态与异常

| 现象 | Agent 应对 |
|------|-----------|
| `check_rollinggo.py` 失败 / 无 Key | 提示前往 [rollinggo.store](https://rollinggo.store/) 申请 Key，检查 `.env` 中 `ROLLINGGO_API_KEY` |
| API 返回 `success: false` 或 HTTP 错误 | 告知「查价服务异常」，**不要**说成「无票/无命中」 |
| 预估 **>500 次** 且用户未确认 | 展示两种模式预估，拒绝执行全量穷举 |
| `parse_nl_intent` 有 `errors` | 向用户澄清缺失字段（出发地、日期、预算等）后再查价 |
| 命中数为 0 且 API 正常 | 说明当前条件下暂无符合预算/日期的报价，建议放宽预算或日期 |

## 域知识

### RollingGo

- API：`https://mcp.rollinggo.cn/api/mcp/flightsearch`
- MCP 服务名：`RollingGo-Flight`（单次补查可用）
- streamable-http 需 `Accept: application/json, text/event-stream`

### 日期语义

| 表述 | 日期窗 |
|------|--------|
| 国庆 | 10-01 ~ 10-07 |
| 国庆前后 | 09-28 ~ 10-10 |

### 路线展示

- 往返：`北京 ⇄ 曼谷`
- 开口程：`天津 → 马尼拉 · 棉兰 → 天津` 或者 ：`北京 → 曼谷 · 普吉 → 天津` 或者：`北京 → 曼谷 · 曼谷 → 天津`

## 脚本一览

| 脚本 | 作用 |
|------|------|
| `config.py` | `.env` / Key 加载 |
| `check_rollinggo.py` | 连通性自检 |
| `parse_nl_intent.py` | 自然语言 → SearchIntent |
| `run_search.py` | 精简 / 全量穷举实时查价 |
| `generate_flight_report.py` | 分页 HTML 报告 |
| `flight_search_engine.py` | 查价引擎 |

## 示例

**用户**：北京出发，日本菲律宾国庆期间航班价格。

**Agent**：

1. `parse_nl_intent.py` 解析意图并写入 `output/intent.json`
2. 展示精简模式与全量穷举的预估次数，请用户选择
3. `run_search.py --mode smart` 或 `--mode exhaustive` 查价（对用户只说明中文模式名）
4. `generate_flight_report.py` 出报告并汇报 summary

---
