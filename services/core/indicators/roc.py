from __future__ import annotations

from decimal import Decimal

from services.core.indicators.base import BarDataPoint, IndicatorOutput
from services.core.indicators.utils import quantize_decimal


class ROCIndicator:
    name = "roc"

    def __init__(self, period: int = 12) -> None:
        self.period = period

    def compute(self, bars: list[BarDataPoint]) -> list[IndicatorOutput]:
        outputs: list[IndicatorOutput] = []
        signature = f"period={self.period}"
        for index in range(self.period, len(bars)):
            previous_close = bars[index - self.period].close
            roc = Decimal("0") if previous_close == 0 else ((bars[index].close - previous_close) / previous_close) * Decimal("100")
            outputs.append(
                IndicatorOutput(
                    trade_date=bars[index].trade_date,
                    indicator_name=self.name,
                    component="value",
                    parameter_signature=signature,
                    value=quantize_decimal(roc),
                )
            )
        return outputs
