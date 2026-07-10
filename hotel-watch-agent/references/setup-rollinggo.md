# 从零接入 RollingGo 酒店 MCP

本文说明如何在 **Cursor、Claude Code、Codex、OpenClaw** 等 Agent 中安装 `hotel-watch-agent` 并完成 RollingGo 酒店 Key 配置。

整体顺序：**申请 Key → 安装 Skill → 配置 `.env` → 自检 →（可选）配置 MCP**。

---

## 1. 前置条件

| 项 | 要求 |
|----|------|
| Python | 3.8+，终端可执行 `python3` |
| Agent | 支持 Skills 协议（能加载 `SKILL.md`） |
| RollingGo Key | 酒店 MCP Key，格式 `mcp_...` |
| 网络 | 可访问 `https://mcp.rollinggo.cn` |

---

## 2. 申请 API Key

1. 打开 **[rollinggo.store](https://rollinggo.store/)**（文档：[rollinggo.store/docs](https://rollinggo.store/docs)）
2. 注册账号并申请 **MCP API Key**（以 `mcp_` 开头）
3. 妥善保管 Key，**勿提交到 Git 或公开分享**

同一 Key 通常可用于 RollingGo 航班与酒店服务；本 Skill 使用 **RollingGo-Hotel** 相关接口。

---

## 3. 安装 Skill

**推荐（skills.sh，自动适配 Agent）**：

```bash
npx skills add sxyfe/skills@hotel-watch-agent -g -y
```

**手动安装**：将 `hotel-watch-agent` 目录链接或复制到 Agent 的 Skills 目录：

| Agent | 常见 Skills 目录 |
|-------|------------------|
| Cursor | `~/.cursor/skills/hotel-watch-agent` |
| Claude Code | 项目 `.claude/skills/hotel-watch-agent` 或 `~/.claude/skills/` |
| 其他 | 查阅该 Agent 文档中的 Skills 路径 |

```bash
# 示例：克隆 monorepo 后链接到 Cursor
git clone https://github.com/sxyfe/skills.git
ln -s "$(pwd)/skills/skills/hotel-watch-agent" ~/.cursor/skills/hotel-watch-agent
```

安装后 **新开 Agent 对话**或重启 Agent，以加载 `SKILL.md`。

---

## 4. 配置 API Key（脚本主路径，推荐）

本 Skill 的 Python 脚本（`check_rollinggo_hotel.py`、`run_watch_round.py` 等）**优先读取 Skill 根目录下的 `.env`**。

在 **Skill 根目录**（含 `SKILL.md` 的目录）执行：

```bash
cp .env.example .env
```

编辑 `.env`：

```bash
ROLLINGGO_API_KEY=mcp_你的密钥
```

或临时导出（不写文件）：

```bash
export ROLLINGGO_API_KEY=mcp_你的密钥
```

---

## 5. 连通性自检

仍在 Skill 根目录：

```bash
python3 scripts/check_rollinggo_hotel.py
```

成功时输出类似：`OK: RollingGo 酒店 MCP 连通正常`。

失败时请检查 Key 是否正确、网络是否可达，参见下文「常见问题」。

---

## 6. 配置 MCP（可选）

若 Agent 支持 MCP 且需在对话中直接调用 RollingGo 工具，可参考 `templates/mcp.json.example` 添加 **RollingGo-Hotel** 服务。

示例片段：

```json
{
  "mcpServers": {
    "RollingGo-Hotel": {
      "url": "https://mcp.rollinggo.cn/mcp",
      "type": "streamable-http",
      "headers": {
        "Authorization": "Bearer mcp_你的密钥",
        "Accept": "application/json, text/event-stream"
      }
    }
  }
}
```

各 Agent 配置文件位置不同，将上述片段合并到对应 MCP 配置即可：

| Agent | 常见 MCP 配置位置 |
|-------|-------------------|
| Cursor | `~/.cursor/mcp.json` |
| Claude Code | 项目或用户级 MCP 配置（见官方文档） |
| 其他 | 查阅该 Agent 的 MCP 接入说明 |

修改后重启 Agent 或重载 MCP。服务名在界面中可能显示为 `RollingGo-Hotel` 或 `user-RollingGo-Hotel`。

**说明**：即使未配置 MCP，只要 `.env` 中 Key 有效，本 Skill 的脚本仍可独立完成查价与监控闭环。MCP 主要用于 Agent 内单次补查或调试。

---

## 7. 在 Agent 中使用

配置完成后，在 Agent 对话中用自然语言描述监控需求，例如：

- 「帮我监控东京这几家酒店，12 月入住，1500 以内降价通知我」
- 「用全球通用预设创建 watch-config，先预估 API 次数」

Agent 将按 `SKILL.md` 执行：分步访谈 → 预估 → 用户确认 → `run_watch_round.py` → 有触发时三链告警。

首次可让 Agent 执行 **最小成功路径**（见 `SKILL.md`）验证环境。

---

## 8. 常见问题

| 现象 | 处理 |
|------|------|
| 401 / 403 | Key 无效或过期，前往 [rollinggo.store](https://rollinggo.store/) 重新申请 |
| `未配置 RollingGo API Key` | 在 Skill 根目录创建 `.env` 并填入 `ROLLINGGO_API_KEY` |
| MCP 工具不可见 | 确认 Agent 已加载 RollingGo-Hotel；或仅用 `.env` + 脚本路径 |
| 查价无结果 | 检查入住日是否为未来日期；酒店 ID 是否正确 |
| 预估 >100 次 | 须向用户展示次数并获确认后再加 `--confirm` 执行 |
| Skill 未生效 | 确认目录在 Agent Skills 路径内，并重开对话 |

---

## 9. 相关文件

| 文件 | 说明 |
|------|------|
| `.env.example` | Key 配置模板 |
| `templates/mcp.json.example` | MCP 配置模板 |
| `scripts/check_rollinggo_hotel.py` | 连通性探针 |
| `SKILL.md` | Agent 主工作流指令 |
