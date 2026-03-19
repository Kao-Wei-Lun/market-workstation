from datetime import date, timedelta
from decimal import Decimal

from services.core.indicators.base import BarDataPoint
from services.core.indicators.ema import EMAIndicator


def test_ema_uses_sma_seed_and_recursive_smoothing() -> None:
    bars = [
        BarDataPoint(
            trade_date=date(2024, 1, 1) + timedelta(days=index),
            close=Decimal(str(value)),
            high=Decimal(str(value)),
            low=Decimal(str(value)),
            volume=100,
        )
        for index, value in enumerate([10, 11, 12, 13])
    ]

    outputs = EMAIndicator(period=3).compute(bars)

    assert [item.value for item in outputs] == [Decimal("11.000000"), Decimal("12.000000")]
