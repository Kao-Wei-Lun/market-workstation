from __future__ import annotations

from services.core.indicators.base import BarDataPoint, IndicatorOutput
from services.core.indicators.utils import decimal_mean, quantize_decimal


class SMAIndicator:
    name = "sma"

    def __init__(self, period: int) -> None:
        self.period = period

    def compute(self, bars: list[BarDataPoint]) -> list[IndicatorOutput]:
        outputs: list[IndicatorOutput] = []
        for index in range(self.period - 1, len(bars)):
            window = [bar.close for bar in bars[index + 1 - self.period : index + 1]]
            outputs.append(
                IndicatorOutput(
                    trade_date=bars[index].trade_date,
                    indicator_name=self.name,
                    component="value",
                    parameter_signature=f"period={self.period}",
                    value=quantize_decimal(decimal_mean(window)),
                )
            )
        return outputs
