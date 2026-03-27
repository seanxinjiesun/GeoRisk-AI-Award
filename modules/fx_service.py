from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import requests


@dataclass
class FxRateResult:
    usd_cny: float
    source: str
    is_fallback: bool
    fetched_at: str


def get_usd_cny_rate() -> FxRateResult:
    fallback = 7.2
    url = "https://open.er-api.com/v6/latest/USD"

    try:
        resp = requests.get(url, timeout=6)
        resp.raise_for_status()
        data = resp.json()
        rate = float(data.get("rates", {}).get("CNY"))
        if rate <= 0:
            raise ValueError("invalid rate")
        return FxRateResult(
            usd_cny=round(rate, 4),
            source="open.er-api.com",
            is_fallback=False,
            fetched_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
    except Exception:
        return FxRateResult(
            usd_cny=fallback,
            source="fallback(7.2)",
            is_fallback=True,
            fetched_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
