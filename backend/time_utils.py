from __future__ import annotations

from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))


def now_ist() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
