from __future__ import annotations

from decimal import Decimal

from services.core.indicators.base import BarDataPoint, IndicatorOutput
from services.core.indicators.utils import decimal_mean, quantize_decimal


class EMAIndicator:
    name = "ema"

    def __init__(self, period: int) -> None:
        self.period = period

    def compute(self, bars: list[BarDataPoint]) -> list[IndicatorOutput]:
        if len(bars) < self.period:
            return []

        multiplier = Decimal("2") / Decimal(self.period + 1)
        seed = decimal_mean([bar.close for bar in bars[: self.period]])
        outputs = [
            IndicatorOutput(
                trade_date=bars[self.period - 1].trade_date,
                indicator_name=self.name,
                component="value",
                parameter_signature=f"period={self.period}",
                value=quantize_decimal(seed),
            )
        ]
        previous = seed
        for bar in bars[self.period :]:
            previous = ((bar.close - previous) * multiplier) + previous
            outputs.append(
                IndicatorOutput(
                    trade_date=bar.trade_date,
                    indicator_name=self.name,
                    component="value",
                    parameter_signature=f"period={self.period}",
                    value=quantize_decimal(previous),
                )
            )
        return outputs
