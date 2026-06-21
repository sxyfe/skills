"""中国节假日窗口解析（future-aware）。"""
from __future__ import annotations

from datetime import date


def _window_for_year(year: int, start_md: tuple[int, int], end_md: tuple[int, int]) -> tuple[str, str]:
    start = date(year, start_md[0], start_md[1])
    end = date(year, end_md[0], end_md[1])
    return start.isoformat(), end.isoformat()


def resolve_national_day_window(query: str, ref_date: date | None = None) -> tuple[str, str] | None:
    """解析国庆相关关键词，返回 future-valid 的 (date_start, date_end)。

    - 「国庆前后」→ 09-28 ~ 10-10
    - 「国庆」（不含前后）→ 10-01 ~ 10-07
    """
    ref = ref_date or date.today()
    q = query.replace(" ", "")

    if "国庆前后" in q or "国庆节前后" in q:
        start_md, end_md = (9, 28), (10, 10)
    elif "国庆" in q:
        start_md, end_md = (10, 1), (10, 7)
    else:
        return None

    year = ref.year
    date_start, date_end = _window_for_year(year, start_md, end_md)
    if date.fromisoformat(date_end) < ref:
        year += 1
        date_start, date_end = _window_for_year(year, start_md, end_md)
    return date_start, date_end
