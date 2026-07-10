---
name: hotel-watch-agent
description: >-
  RollingGo 全球酒店价格监控：分步配置、A/B 双层预算、售罄回补、组合触发、三链告警、
  cron+Agent 定时。用户说「酒店监控」「降价提醒」「有房通知」「RollingGo 酒店」「盯价」时使用。
  适配 Cursor、Claude Code、Codex、OpenClaw 等支持 Skills 协议的 Agent 工具。
---

# Hotel Watch Agent

RollingGo 酒店查价 → state JSON → 条件触发告警（三链输出）。

## 安装与配置（引导用户）

用户询问「怎么安装 / 怎么用 / 需要什么 Key」时，按以下顺序说明（适配 Cursor、Claude Code、Codex、OpenClaw 等 Skills 协议 Agent）：

### 前置条件

- **Python 3.8+**（终端可执行 `python3`）
- **RollingGo 酒店 MCP Key**：在 [rollinggo.store](https://rollinggo.store/) 申请，格式 `mcp_...`（文档 [rollinggo.store/docs](https://rollinggo.store/docs)）
- 所用 Agent 已支持 Skills（能加载本目录 `SKILL.md`）

### 安装 Skill

**推荐（skills.sh）**：

```bash
npx skills add sxyfe/skills@hotel-watch-agent -g -y
```

**手动**：将本 Skill 目录链接或复制到 Agent 的 Skills 目录，例如 Cursor `~/.cursor/skills/hotel-watch-agent`、Claude Code `.claude/skills/hotel-watch-agent`。安装后新开对话或重启 Agent。

### 配置 Key

在 **Skill 根目录**（本文件所在目录）：

```bash
cp .env.example .env
# 编辑 .env：ROLLINGGO_API_KEY=mcp_...
python3 scripts/check_rollinggo_hotel.py
```

自检通过后再查价。**无 Key 时禁止调用查价脚本**，须引导用户完成上述配置。详见 `references/setup-rollinggo.md`。

可选：Agent 若支持 MCP，可参考 `templates/mcp.json.example` 配置 RollingGo-Hotel；脚本**优先读 `.env`**。

### 在 Agent 中使用

配置完成后，用户用自然语言描述监控需求（如「监控青森温泉 10 月入住，700 以内降价或有房通知我」）。Agent 执行本 Skill 工作流：分步访谈 → 预估 API → 用户确认 → 查价 → 更新 state → 有触发时三链告警。

## 最小成功路径（首次用户）

在 Skill 根目录依次执行：

```bash
python3 scripts/check_rollinggo_hotel.py

python3 scripts/init_watch_config.py --preset generic-worldwide -o ./output

python3 scripts/estimate_watch.py --config ./output/my-watch-config.json --json

python3 scripts/run_watch_round.py \
  --config ./output/my-watch-config.json \
  --state ./output/my-hotel-watch.json \
  --confirm
```

## 前置条件（必读）

1. 已完成上文 **[安装与配置](#安装与配置引导用户)**：Skill 已安装、`.env` 已填 Key、`check_rollinggo_hotel.py` 已通过
2. 若用户尚未配置 Key → 引导前往 [rollinggo.store](https://rollinggo.store/) 申请并写入 `.env`，**不得**跳过直接查价

## 硬约束

- watchlist **≤ 10 家**
- 每入住日默认 **1 晚**（非连住）
- 禁止高频刷接口、公开共享 Key
- 预估 **>100 次 API** 须用户确认后才可 `--confirm` 执行
- 定时间隔建议 **≥12h**

## 何时使用

- 用户要监控酒店价格、有房/售罄、降价提醒
- 用户提到 A/B 预算、组合触发、定时查价、cron
- 用户说「RollingGo 酒店」「hotel watch」「盯价」

## 工作流

```
访谈/预设 → watch-config.json → estimate → 用户确认 → run_watch_round
    → 更新 state → 单点/组合 triggers → 告警或静默
         ↑
    外部 cron ──▶ Agent（格式化/异常）
```

## Phase 1 · 分步访谈

逐步询问（`references/interview-checklist.md`）：

1. 国家 + 地点 + 酒店（≤10，`hotelId:名称/tier`）
2. 入住日 + 人数
3. 单层预算 **或** A/B 双层（`budgetTiers`）
4. 房型偏好
5. 阈值 + 组合触发 + 单酒店特例
6. 定时（cron + Agent）与静默策略

```bash
python3 scripts/init_watch_config.py --preset generic-worldwide -o ./output
python3 scripts/init_watch_config.py --preset jp-onsen-dual-tier -o ./output
```

预设：`templates/presets/`。示例：`templates/watch-config.example.aomori.json`。

## Phase 2 · 预估 → 确认 → 执行

**Agent MUST**：

```bash
# 1. 预估（不查价）
python3 scripts/estimate_watch.py --config watch-config.json --json

# 2. 向用户展示次数；>100 次须确认

# 3. 执行一轮
python3 scripts/run_watch_round.py --config watch-config.json --state state.json --confirm
```

stdout 为 JSON：`triggered`、`alerts`、`silentUnlessTriggered`。

### 精查逻辑

watchlist 每家 × 每入住日 → `getHotelDetail`；可选 `searchHotels` 广度扫。

1. `roomPreferences` 过滤（`references/room-type-matching.md`）
2. 取最低 `totalPrice`；按 tier 应用 `budgetTiers`
3. 三链（`references/booking-links.md`）

### 状态文件

路径：`meta.stateFile`。结构见 `references/state-schema.md`。

### 触发

- 单点：`references/trigger-rules.md`（restock / drop / halfBoard …）
- 组合：`compositeTriggers`（跨晚 distinct-hotels-per-night 等）
- 特例：`hotelOverrides` / `hotel-date-price-cross`

### 告警

`templates/alert-message.template.md` + 三链脚本：

```bash
python3 scripts/extract_booking_links.py detail.json --hotel-name "..." --city "..."
```

## Phase 3 · 外部 cron + Agent

```bash
python3 scripts/render_loop_prompt.py --config watch-config.json --mode both
```

- `{slug}-loop-prompt.txt` — Agent 每轮指令
- `{slug}-cron-prompt.txt` — crontab 示例

详见 `references/scheduling-optional.md`。推荐：**cron 跑 `run_watch_round.py`，有触发再唤 Agent**。

多任务：

```bash
python3 scripts/render_loop_prompt.py --combine aomori.json hakodate.json -o ./output
```

## 失败态与异常

| 现象 | Agent 应对 |
|------|-----------|
| `check_rollinggo_hotel.py` 失败 / 无 Key | 提示前往 [rollinggo.store](https://rollinggo.store/) 申请 Key，检查 `.env` |
| MCP / API 调用失败 | 告知「查价服务异常」，检查 Key 与网络 |
| 预估 **>100 次** 且用户未确认 | 展示预估次数，拒绝执行直至用户确认 |
| `silentUnlessTriggered=true` 且无触发 | 正常；state 已更新，无需向用户告警 |
| watchlist >10 家 | 拒绝配置，要求缩减清单 |

## MCP

服务名常为 **RollingGo-Hotel** 或 **user-RollingGo-Hotel**。工具见 `references/mcp-tools.md`。

| 工具 | 用途 |
|------|------|
| `searchHotels` | 全球区域+标签+预算扫描 |
| `getHotelDetail` | 单酒店房型/plan/价格 |
| `getHotelSearchTags` | 标签参考 / 自检 |

## 脚本

| 脚本 | 作用 |
|------|------|
| `check_rollinggo_hotel.py` | MCP 连通性 |
| `init_watch_config.py` | 分步 CLI + 预设 |
| `estimate_watch.py` | API 预估 |
| `run_watch_round.py` | **一轮监控闭环** |
| `render_loop_prompt.py` | loop/cron/combined prompt |
| `extract_booking_links.py` | 三链 |
| `evaluate_triggers.py` | 离线单点触发测试 |

## 反滥用

个人合理监控；定时间隔 ≥12h。大量酒店/多日期 **必须先 estimate 并获用户确认**。

## 示例

**用户**：帮我监控青森几家温泉，10 月入住，700 以内降价或有房通知我。

**Agent**：

1. 确认 Key 与自检已通过
2. 分步访谈或 `--preset jp-onsen-dual-tier` 生成 `watch-config.json`
3. `estimate_watch.py` 展示预估，>100 次须用户确认
4. `run_watch_round.py --confirm` 执行一轮
5. 有触发时格式化三链告警；无触发则说明 state 已更新

---
