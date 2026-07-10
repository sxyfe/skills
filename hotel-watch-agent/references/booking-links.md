# 下单链接（三链）

告警表格须同时列出：**携程 | 去哪儿 | RollingGo**。

## 提取优先级

1. **API 内嵌 URL**：递归扫描响应中 `ctrip.com` / `trip.com` / `qunar.com`（若 plan `metadata` 未来提供）
2. **RollingGo**：`getHotelDetail.bookingUrl` 或按 hotelId+日期构造
3. **搜索 fallback**（API 无 OTA 直链时）：
   - 携程：`https://hotels.ctrip.com/hotels/list?keyword=酒店名+城市`
   - 去哪儿：城市搜索页 + 入住日参数

> 实测 2026-06：茶花宿屋详情 API 仅返回 RollingGo `bookingUrl`；携程/去哪儿列为搜索入口，非 deep link 下单页。有直链时优先展示直链。

## 脚本

```bash
python3 scripts/extract_booking_links.py detail.json --hotel-name "茶花宿屋" --city "青森"
```
