from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

from services.core.indicators.base import BarDataPoint


@pytest.fixture
def indicator_bars() -> list[BarDataPoint]:
    bars: list[BarDataPoint] = []
    base_date = date(2024, 1, 1)
    for index in range(80):
        close = Decimal("100") + Decimal(index) + (Decimal(index % 5) / Decimal("2"))
        high = close + Decimal("2") + Decimal(index % 3)
        low = close - Decimal("2") - Decimal((index + 1) % 2)
        volume = 1_000 + (index * 25) + ((index % 4) * 100)
        bars.append(
            BarDataPoint(
                trade_date=base_date + timedelta(days=index),
                close=close,
                high=high,
                low=low,
                volume=volume,
            )
        )
    return bars
