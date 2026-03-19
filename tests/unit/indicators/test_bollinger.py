from datetime import date, timedelta
from decimal import Decimal

from services.core.indicators.base import BarDataPoint
from services.core.indicators.bollinger import BollingerBandsIndicator


def test_bollinger_bands_return_upper_middle_and_lower_components() -> None:
    bars = [
        BarDataPoint(
            trade_date=date(2024, 1, 1) + timedelta(days=index),
            close=Decimal(str(100 + index)),
            high=Decimal(str(100 + index)),
            low=Decimal(str(100 + index)),
            volume=100,
        )
        for index in range(25)
    ]

    outputs = BollingerBandsIndicator(period=20, stddev_multiplier=2).compute(bars)
    latest = [item for item in outputs if item.trade_date == bars[-1].trade_date]
    component_map = {item.component: item.value for item in latest}

    assert {"upper_band", "middle_band", "lower_band"} == set(component_map)
    assert component_map["upper_band"] > component_map["middle_band"] > component_map["lower_band"]
