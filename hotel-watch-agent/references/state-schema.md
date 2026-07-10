# 状态文件 schema（runtime state）

路径由 `watch-config.meta.stateFile` 指定。与 **config** 分离：config 只读，state 每轮更新。

## 顶层结构

```json
{
  "meta": {
    "version": 2,
    "slug": "aomori-onsen",
    "lastCheckAt": "2026-06-27T08:00:00+08:00",
    "lastApiEstimate": { "total": 36, "getHotelDetail": 30, "searchHotels": 6 }
  },
  "baseline": {},
  "lastSnapshot": {},
  "alertsSent": [],
  "lastRunTriggers": [],
  "compositeState": {}
}
```

## baseline / lastSnapshot

按 `hotelId → checkInDate → snapshot` 嵌套：

```json
{
  "price": 489,
  "available": true,
  "halfBoard": false,
  "tier": "ryokan",
  "matchedRoomPlan": { "roomNameCn": "...", "ratePlanName": "...", "totalPrice": 489 },
  "links": { "ctrip": "...", "qunar": "...", "rollinggo": "..." },
  "bookingUrl": "https://rollinggo.cn/..."
}
```

| 字段 | 说明 |
|------|------|
| `price` | 过滤后最低 `totalPrice`（CNY）；售罄为 `null` |
| `available` | 是否有可订 plan |
| `halfBoard` | `true` / `false` / `"pending"` |
| `baseline` | 首次有效查价或用户确认后写入，作为降幅对比基准 |
| `lastSnapshot` | 每轮覆盖，供下轮 restock/drop 对比 |

## alertsSent（防重复）

```json
{
  "key": "617324|2027-02-08|restock",
  "at": "2026-06-08T12:00:00+08:00",
  "price": 750
}
```

相同 `key` 已存在且价格未进一步变化 → 跳过告警。价格继续下降可再次触发 `drop-*`。

## lastRunTriggers

本轮触发的规则 ID 列表（含 composite id），供 Agent 格式化告警。

## compositeState

组合触发辅助状态，如 `distinct-hotels-per-night` 上次是否已满足，避免重复刷屏。
