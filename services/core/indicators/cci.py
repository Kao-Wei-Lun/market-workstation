from __future__ import annotations

from decimal import Decimal

from services.core.indicators.base import BarDataPoint, IndicatorOutput
from services.core.indicators.utils import decimal_mean, quantize_decimal


class CCIIndicator:
    name = "cci"

    def __init__(self, period: int = 20) -> None:
        self.period = period

    def compute(self, bars: list[BarDataPoint]) -> list[IndicatorOutput]:
        typical_prices = [(bar.high + bar.low + bar.close) / 3 for bar in bars]
        outputs: list[IndicatorOutput] = []
        signature = f"period={self.period}"
        for index in range(self.period - 1, len(bars)):
            window = typical_prices[index + 1 - self.period : index + 1]
            sma = decimal_mean(window)
            mean_deviation = decimal_mean([abs(value - sma) for value in window])
            cci = Decimal("0") if mean_deviation == 0 else (typical_prices[index] - sma) / (Decimal("0.015") * mean_deviation)
            outputs.append(
                IndicatorOutput(
                    trade_date=bars[index].trade_date,
                    indicator_name=self.name,
                    component="value",
                    parameter_signature=signature,
                    value=quantize_decimal(cci),
                )
            )
        return outputs
