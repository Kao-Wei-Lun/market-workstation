from __future__ import annotations

from decimal import Decimal

from services.core.indicators.base import BarDataPoint, IndicatorOutput
from services.core.indicators.utils import quantize_decimal


class RSIIndicator:
    name = "rsi"

    def __init__(self, period: int = 14) -> None:
        self.period = period

    def compute(self, bars: list[BarDataPoint]) -> list[IndicatorOutput]:
        if len(bars) <= self.period:
            return []

        closes = [bar.close for bar in bars]
        gains: list[Decimal] = []
        losses: list[Decimal] = []
        for previous, current in zip(closes, closes[1:]):
            change = current - previous
            gains.append(max(change, Decimal("0")))
            losses.append(abs(min(change, Decimal("0"))))

        average_gain = sum(gains[: self.period], Decimal("0")) / Decimal(self.period)
        average_loss = sum(losses[: self.period], Decimal("0")) / Decimal(self.period)
        outputs = [
            IndicatorOutput(
                trade_date=bars[self.period].trade_date,
                indicator_name=self.name,
                component="value",
                parameter_signature=f"period={self.period}",
                value=self._calculate_rsi(average_gain, average_loss),
            )
        ]

        for index in range(self.period, len(gains)):
            average_gain = ((average_gain * Decimal(self.period - 1)) + gains[index]) / Decimal(self.period)
            average_loss = ((average_loss * Decimal(self.period - 1)) + losses[index]) / Decimal(self.period)
            outputs.append(
                IndicatorOutput(
                    trade_date=bars[index + 1].trade_date,
                    indicator_name=self.name,
                    component="value",
                    parameter_signature=f"period={self.period}",
                    value=self._calculate_rsi(average_gain, average_loss),
                )
            )
        return outputs

    @staticmethod
    def _calculate_rsi(average_gain: Decimal, average_loss: Decimal) -> Decimal:
        if average_loss == 0:
            return Decimal("100.000000")
        relative_strength = average_gain / average_loss
        return quantize_decimal(Decimal("100") - (Decimal("100") / (Decimal("1") + relative_strength)))
