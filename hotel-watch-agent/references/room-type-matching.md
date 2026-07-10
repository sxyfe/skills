# 房型匹配

从 `roomRatePlans` 中筛选符合 `roomPreferences` 的 plan，再取最低 `totalPrice`。

## 匹配字段

默认扫描：`roomName`、`roomNameCn`、`bedTypeDescription`、`ratePlanName`（不区分大小写）。

## 逻辑

1. 若 plan 文本命中任一 `excludeKeywords` → 排除
2. 若 `keywords` 为空 → 所有有价 plan 参与比价
3. 若 `keywords` 非空 → 须命中至少一个关键词（或预设别名）
4. 无匹配 plan → 该晚 `available: false`（房型维度），与「真售罄」区分时可记 `roomMismatch: true`

## 预设别名

见 `scripts/hotel_utils.py` 中 `ROOM_TYPE_PRESETS`。
