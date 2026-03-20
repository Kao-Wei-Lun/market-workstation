from __future__ import annotations

from services.core.indicators.base import BarDataPoint, IndicatorOutput
from services.core.indicators.utils import quantize_decimal, true_range_series, wilder_smoothing


class ATRIndicator:
    name = "atr"

    def __init__(self, period: int = 14) -> None:
        self.period = period

    def compute(self, bars: list[BarDataPoint]) -> list[IndicatorOutput]:
        true_ranges = true_range_series(bars)
        smoothed = wilder_smoothing(true_ranges, self.period)
        outputs: list[IndicatorOutput] = []
        for index, value in enumerate(smoothed):
            if value is None:
                continue
            atr_value = quantize_decimal(value / self.period)
            outputs.append(
                IndicatorOutput(
                    trade_date=bars[index].trade_date,
                    indicator_name=self.name,
                    component="value",
                    parameter_signature=f"period={self.period}",
                    value=atr_value,
                )
            )
        return outputs
