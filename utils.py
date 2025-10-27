# utils.py

from datetime import date, timedelta
from typing import List

def parse_date(x):
    if not x:
        return None
    if hasattr(x, "isoformat"):
        return x.isoformat()
    return str(x)

def today_ymd() -> str:
    return date.today().isoformat()

def upcoming_days(n: int) -> List[str]:
    t = date.today()
    return [(t + timedelta(days=i)).isoformat() for i in range(n)]
