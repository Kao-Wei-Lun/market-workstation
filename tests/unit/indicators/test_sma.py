from datetime import date, timedelta
from decimal import Decimal

from services.core.indicators.base import BarDataPoint
from services.core.indicators.sma import SMAIndicator


def test_sma_matches_simple_rolling_average() -> None:
    bars = [
        BarDataPoint(
            trade_date=date(2024, 1, 1) + timedelta(days=index),
            close=Decimal(str(value)),
            high=Decimal(str(value)),
            low=Decimal(str(value)),
            volume=100,
        )
        for index, value in enumerate([1, 2, 3, 4, 5])
    ]

    outputs = SMAIndicator(period=3).compute(bars)

    assert [item.value for item in outputs] == [Decimal("2.000000"), Decimal("3.000000"), Decimal("4.000000")]
