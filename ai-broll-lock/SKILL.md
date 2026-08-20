---
name: ai-broll-lock
description: >
  Generates 4–8s B-roll clips from timeline.json broll shots while locking one look-ref image
  for character and scene consistency. Use when ai-host-tutorial needs metaphor footage, or the
  user says 定妆空镜、角色一致、图生视频 B-roll、/ai-broll-lock. Does not generate readable
  UI, does not replace screen evidence, and does not skip the look-ref gate.
disable-model-invocation: true
---

# 空镜定妆

输入：`work/timeline.json` 的 `type=broll` 镜头 + 一张定妆图 `inputs/look-ref.png`（或用户指定路径）。  
输出：`outputs/broll/<shot-id>.mp4`，路径写回 timeline 的 `asset` 和 job-state `tracks.broll`。  
禁止回读主编排 skill。空镜不必对口型。

## 步骤

1. 没有 `broll` 镜头：`gates.broll=skipped`，结束。
2. 没有定妆图：停。向用户要一张角色或场景静帧。不要凭空文生一张「以后当定妆」。
3. 把定妆路径写入 `tracks.broll.look_ref`。
4. 付费图生视频前向用户确认。用户未批准就停。
5. 每一镜单独出 4–8 秒：
   - 图生视频，参考图始终是同一张定妆
   - prompt 用该镜 `broll_prompt`，并追加同一句锁定词：同一张脸、同一套衣服、同一场景陈设，禁止出现可读屏幕文字
   - 时长夹在该镜 `end_s - start_s` 与 8 秒之间
6. 下载到 `outputs/broll/<id>.mp4`。文件损坏先重下，不要立刻重新生成。
7. 更新 `shots[].asset`、`tracks.broll.clips`。全部成功则 `gates.broll=done`。

## 一致性

- 全片共用一张定妆。中途换脸等于另一条片。
- 服装、房间陈设写进每条 prompt 的固定前缀，从定妆图描述里抄，不要每镜重新发明房间。
- 写实口播人不是这套空镜。空镜角色可以是 3D/插画，只要全片空镜彼此一致。
- 失败镜标注 `asset=null` 并停在该镜，问用户跳过还是换 prompt，不要默默用另一张脸补上。

## 工具默认

用户指定厂商就用用户的。未指定时：图生视频用当前可用的 Kling / Hailuo / Seedance / Runway 之一，并在 job-state 记下实际用的名称。参数以厂商当前文档为准，不要把过期价目写进流程。

本地 LivePortrait 只适合「静图微动」。有明显位移、过肩、翻书的镜头走图生视频。
