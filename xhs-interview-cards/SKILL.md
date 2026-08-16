---
name: xhs-interview-cards
description: 从真实公开访谈生产小红书人物访谈截图笔记（今日候选、抽金句、写正文、按金句时段截不同画面做成花卷式字幕条、ledger 去重）。在用户说人物访谈截图、今日候选、访谈金句、花卷截图、做一篇访谈、/xhs-interview-cards 时使用。
---

# 人物访谈截图

一套生产系统，多个号分发。第一版只落到本地，不自动发布。

命令入口：

```bash
python3 {baseDir}/scripts/cli.py status
```

`{baseDir}` = 本 SKILL.md 所在目录。成品根目录优先读环境变量 `XHS_INTERVIEW_CONTENT_ROOT`，其次 `config.local.json`，再次 `config.json` 的 `content_root`。本机路径只写进 `config.local.json`，不要提交。

```bash
cp {baseDir}/config.example.json {baseDir}/config.local.json
# 把 content_root 改成你的成品目录
python3 {baseDir}/scripts/cli.py status
```

## 非谈判项

- 金句必须来自可核验的公开访谈。没有源就不做这个人
- 不编造名人原话，不用 AI 生成假访谈画面
- 人物池是开放的：种子名单只是冷启动，不是白名单
- 同一段原话跨号也不能再用
- 同一场访谈可做多篇；金句多、主题明显不同时，拆成 2～3 篇小文，不要塞进一篇
- 同一人在同一号上默认 7 天冷却；同场拆出的多篇可以一次生产、同日发布，不受冷却拦截（冷却管的是「换一场访谈再做这个人」）
- 没链接先出候选，用户确认后再生产
- 下载失败就停，改要本地视频。不绕过登录、付费墙、加密
- 读 `{baseDir}/references/safety.md`：不承诺涨粉或收入，不编造原话，不把本机路径和登录态写进仓库

## 命令

用户意图映射：

| 用户说 | 走哪条 |
|---|---|
| 今日候选 / 出候选 / 每天扫描 | `candidates` |
| 做这篇 / 生产 / 指定人物或链接 | `produce` |
| 记下来 / 入库 / 补档 | `record`（produce 结束时必须跑） |

先跑 `python3 {baseDir}/scripts/cli.py status`。

## candidates

1. 读 `{baseDir}/references/candidate-search.md` 和 ledger
2. 冷却中的「账号 + 人物」不要作为今日主推
3. 种子人物优先找未用角度；同时搜池外有公开访谈的人
4. 源范围：YouTube、B 站、播客公开页、已发表采访稿。没有可核验 URL 的丢掉
5. 每号 3～5 条候选，科技号和女性号都给

输出格式：

```markdown
## 今日候选

### tech
1. 人物 | 源标题 | URL | 日期 | 有无字幕 | 拟切角度 | 冷却是否通过
...

### women
...
```

停在这里。用户点编号、改人物、或丢链接之后才进入 produce。

## produce

输入至少要有：`account`（tech|women）+ 人物 + 已确认的 `source_url` 或本地视频。

1. `cli.py cooldown --account ... --person ...`  
   退出码 2 就停，除非用户明确要求强制
2. 抽文稿（必须先拿到文字，再抽金句）。只走这一条命令：

   ```bash
   python3 {baseDir}/scripts/cli.py transcript --url 'https://...' --out-dir {content_root}/_cache/transcripts/{id}
   # 或本地视频：
   python3 {baseDir}/scripts/cli.py transcript --video '/path/to.mp4' --out-dir {content_root}/_cache/transcripts/{id}
   ```

   读产出的 `transcript.txt`，有 `transcript-timed.txt` 时一并读（给每张卡对时间）。内部路由见 `{baseDir}/references/transcript.md`。没有文稿就停，不要凭印象写金句。
3. 读 `{baseDir}/references/split-articles.md`。先按主题切篇，再写单篇。
   - 一场访谈只支撑一个主题 → 1 篇
   - 金句多、主题明显不同（例如管理 / 人生 / 金钱）→ 拆成 2～3 篇，每篇一个主题、4～6 个分点
   - 不要把三个主题揉进一篇长文；也不要为了凑篇数把同一段原话拆两次
4. 每一篇单独走：抽金句 → `quotes.json` →  
   `cli.py check-quotes --quotes quotes.json`  
   撞车就换角度，不要硬发
5. 读 `{baseDir}/references/copy-style.md` 为每一篇写 `文稿.md`
6. 视频：本地文件优先。只有公开链接且没有本地文件时才  
   `cli.py fetch-video --url URL --out {content_root}/_cache/videos/{id}.mp4`  
   失败就停，让用户补文件
7. 每一篇 `cli.py prepare-dir --account --date --person --title`
8. 把该篇切片写成 `cards.json`。每张卡必须带 `time`（秒或 `00:01:12`），对准这张卡主金句在 `transcript-timed.txt` 里出现的段落。禁止 5～8 张共用同一帧当主体图。
   ```json
   {"cards":[{"header":"...","time":"03:21","lines":["..."]}]}
   ```
   然后用视频按卡截帧（不要先截一张再复用）：
   ```bash
   python3 {baseDir}/scripts/cli.py compose --video {视频} --cards cards.json --out-dir {成品目录}
   ```
   compose 会按 `time` 各截一帧；时间过近或画面过像时自动错开。同场拆篇也各自对金句时间，不要共用一张兜底图。
   只有没有视频、也没有时间轴时，才允许 `--frame` 单帧兜底。
9. 把 `文稿.md` 放进该篇成品目录
10. 每一篇立刻 `record`；同场拆篇时 `entry.json` 加 `"same_interview_split": true`，跳过人物冷却，金句去重仍然生效

## record

`entry.json` 最小字段：

```json
{
  "id": "2026-08-15-tech-person-slug",
  "date": "2026-08-15",
  "account": "tech",
  "person": "梁文锋",
  "title": "标题",
  "source_url": "https://...",
  "source_title": "访谈标题",
  "quotes": ["原话1", "原话2"],
  "output_dir": "tech/2026-08-15-梁文锋-标题"
}
```

```bash
python3 {baseDir}/scripts/cli.py record --entry entry.json
```

## 成品位置

```text
{content_root}/{tech|women}/{日期}-{人物}-{短标题}/
  文稿.md
  01.png
  02.png
```

现有编号目录不要搬。本地旧成品若已进 ledger，保持不动。

## 插队

用户只给人物或主题：先 candidates，确认源再 produce。  
用户给了链接：跳过搜索，仍要 cooldown + 金句去重，然后 produce。
