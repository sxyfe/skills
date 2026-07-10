# RollingGo-Hotel MCP 工具

服务 URL：`https://mcp.rollinggo.cn/mcp`

## searchHotels — 广度扫描

必填：`originQuery`、`place`、`placeType`

```json
{
  "countryCode": "JP",
  "place": "浅虫温泉",
  "placeType": "景点",
  "checkInParam": {
    "checkInDate": "2027-02-08",
    "stayNights": 1,
    "adultCount": 2
  },
  "hotelTags": {
    "requiredTags": ["温泉"],
    "maxPricePerNight": 800
  },
  "originQuery": "日本青森温泉，2027-02-08 入住1晚，2成人，预算800人民币",
  "size": 20
}
```

## getHotelDetail — 精查（每轮必做）

```json
{
  "hotelId": 1074466,
  "dateParam": {
    "checkInDate": "2027-02-08",
    "checkOutDate": "2027-02-09"
  },
  "occupancyParam": {
    "adultCount": 2,
    "roomCount": 1,
    "childCount": 0
  }
}
```

### 关键返回字段（实测）

| 字段 | 用途 |
|------|------|
| `bookingUrl` | RollingGo 详情页（顶层） |
| `roomRatePlans[].totalPrice` | 可订总价 CNY |
| `roomRatePlans[].roomNameCn` | 中文房型名 |
| `roomRatePlans[].bedTypeDescription` | 床型描述 |
| `roomRatePlans[].ratePlanName` | plan 名（含餐判断） |

无 plan 或全部无价 → `available: false`（售罄）。

## getHotelSearchTags

用于连通性自检与标签参考；平台**无「一泊二食」标签**，含餐须从 plan 名判断。
