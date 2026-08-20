# 交接契约

所有子 skill 只认项目里的这两个文件。改对话记录不算交货。

## 目录

```text
<project>/
  inputs/
    script.md
    portrait.jpg          # 口播可选
    voice-source.mp3      # 口播可选
    look-ref.png          # 空镜定妆，可选
    screen/               # 用户放入的录屏/截图
  work/
    job-state.json
    timeline.json
    screen-shotlist.md
    voiceover-full.mp3
    preview-15s.mp3
  outputs/
    preview-15s.mp4
    host-full.mp4
    broll/
    jianying-edl.md
```

## job-state.json

```json
{
  "skill": "ai-host-tutorial",
  "project": "example",
  "created_at": "YYYY-MM-DD",
  "aspect": "3:4",
  "stage": "intake",
  "loudness": { "target_mean_db": -12, "peak_db": 0 },
  "gates": {
    "script": "pending",
    "storyboard": "pending",
    "host_preview": "not_started",
    "host_full": "not_started",
    "screen": "idle",
    "broll": "idle",
    "composite": "pending",
    "precheck": "pending"
  },
  "tracks": {
    "host": {
      "preview": null,
      "full": null,
      "audio": null
    },
    "screen": { "dir": "inputs/screen", "received": [] },
    "broll": { "look_ref": null, "clips": [] },
    "composite": { "edl": "outputs/jianying-edl.md" }
  },
  "ids": {
    "voice_id": null,
    "image_asset_id": null,
    "preview_video_id": null,
    "full_video_id": null
  }
}
```

`stage` 取值：`intake` `storyboard` `host_preview` `host_full` `screen` `broll` `composite` `precheck` `done`。

`gates.screen`：`idle` | `waiting_user` | `received`。  
`gates.broll`：`idle` | `pending` | `done` | `skipped`。  
`gates.host_preview`：`not_started` | `ready` | `approved`。

## timeline.json

```json
{
  "version": 1,
  "aspect": "3:4",
  "duration_s": 90.0,
  "shots": [
    {
      "id": "s01",
      "start_s": 0.0,
      "end_s": 4.0,
      "type": "host",
      "vo_text": "口播原句",
      "visual": "画面怎么摆",
      "overlay": "硬字幕或技巧条",
      "asset": null,
      "screen_file": null,
      "broll_prompt": null
    }
  ]
}
```

`type` 只能是：`host` `screen` `broll` `gfx` `sub`。一条镜头可以同时在 `overlay` 里写字幕；需要独立贴图层再用 `gfx` / `sub`。

时间轴按配音切。画面先行再配音，口型锁不住。
