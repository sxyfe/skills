# ai-host-tutorial

主编排：把 AI 口播教程拆成五轨（口播人、真实录屏、生成空镜、贴图、硬字幕），用 `job-state.json` + `timeline.json` 交接。本 skill 只编排和门禁，不生成界面、不导出成片。

配套子 skill（建议一起装）：

- `tutorial-storyboard`
- `tutorial-screen-capture`
- `ai-broll-lock`
- `tutorial-composite`

口播人像默认交给已安装的 `rachel-digital-human-production`（MiniMax + HeyGen，15 秒预览门禁）。发布前检可选用 `yuwen-publish-precheck`。

```bash
npx skills add sxyfe/skills@ai-host-tutorial -g -y
npx skills add sxyfe/skills@tutorial-storyboard -g -y
npx skills add sxyfe/skills@tutorial-screen-capture -g -y
npx skills add sxyfe/skills@ai-broll-lock -g -y
npx skills add sxyfe/skills@tutorial-composite -g -y
```

调用：`/ai-host-tutorial`。付费 API 不会自动跑。

授权、肖像、声纹、密钥不要提交进仓库。详见 `references/safety.md`。
