from __future__ import annotations

from decimal import Decimal

from services.core.indicators.base import BarDataPoint, IndicatorOutput
from services.core.indicators.utils import quantize_decimal, rolling_max, rolling_min


class WilliamsRIndicator:
    name = "williams_r"

    def __init__(self, period: int = 14) -> None:
        self.period = period

    def compute(self, bars: list[BarDataPoint]) -> list[IndicatorOutput]:
        highest_highs = rolling_max([bar.high for bar in bars], self.period)
        lowest_lows = rolling_min([bar.low for bar in bars], self.period)
        outputs: list[IndicatorOutput] = []
        signature = f"period={self.period}"
        for index, bar in enumerate(bars):
            highest = highest_highs[index]
            lowest = lowest_lows[index]
            if highest is None or lowest is None:
                continue
            denominator = highest - lowest
            value = Decimal("0") if denominator == 0 else ((highest - bar.close) / denominator) * Decimal("-100")
            outputs.append(
                IndicatorOutput(
                    trade_date=bar.trade_date,
                    indicator_name=self.name,
                    component="value",
                    parameter_signature=signature,
                    value=quantize_decimal(value),
                )
            )
        return outputs
