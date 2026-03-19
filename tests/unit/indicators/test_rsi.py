from datetime import date, timedelta
from decimal import Decimal

from services.core.indicators.base import BarDataPoint
from services.core.indicators.rsi import RSIIndicator


def test_rsi_matches_wilder_reference_value() -> None:
    closes = [
        Decimal("44.34"),
        Decimal("44.09"),
        Decimal("44.15"),
        Decimal("43.61"),
        Decimal("44.33"),
        Decimal("44.83"),
        Decimal("45.10"),
        Decimal("45.42"),
        Decimal("45.84"),
        Decimal("46.08"),
        Decimal("45.89"),
        Decimal("46.03"),
        Decimal("45.61"),
        Decimal("46.28"),
        Decimal("46.28"),
    ]
    bars = [
        BarDataPoint(
            trade_date=date(2024, 1, 1) + timedelta(days=index),
            close=close,
            high=close,
            low=close,
            volume=100,
        )
        for index, close in enumerate(closes)
    ]

    outputs = RSIIndicator(period=14).compute(bars)

    assert len(outputs) == 1
    assert outputs[0].value.quantize(Decimal("0.001")) == Decimal("70.464")
