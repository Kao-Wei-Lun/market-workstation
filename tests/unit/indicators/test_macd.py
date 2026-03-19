from datetime import date, timedelta
from decimal import Decimal

from services.core.indicators.base import BarDataPoint
from services.core.indicators.macd import MACDIndicator


def test_macd_returns_line_signal_and_histogram_components() -> None:
    bars = [
        BarDataPoint(
            trade_date=date(2024, 1, 1) + timedelta(days=index),
            close=Decimal(str(100 + index)),
            high=Decimal(str(100 + index)),
            low=Decimal(str(100 + index)),
            volume=100,
        )
        for index in range(40)
    ]

    outputs = MACDIndicator().compute(bars)
    components = {item.component for item in outputs}

    assert {"macd_line", "signal_line", "histogram"} <= components
    assert any(item.component == "histogram" for item in outputs)
