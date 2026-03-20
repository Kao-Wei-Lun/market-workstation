from __future__ import annotations

from decimal import Decimal

from services.core.indicators.base import BarDataPoint, IndicatorOutput
from services.core.indicators.utils import quantize_decimal


class ParabolicSARIndicator:
    name = "parabolic_sar"

    def __init__(self, step: Decimal = Decimal("0.02"), max_step: Decimal = Decimal("0.2")) -> None:
        self.step = step
        self.max_step = max_step

    def compute(self, bars: list[BarDataPoint]) -> list[IndicatorOutput]:
        if len(bars) < 2:
            return []
        uptrend = bars[1].close >= bars[0].close
        sar = bars[0].low if uptrend else bars[0].high
        extreme_point = bars[0].high if uptrend else bars[0].low
        acceleration_factor = self.step
        signature = f"step={self.step},max_step={self.max_step}"
        outputs: list[IndicatorOutput] = []
        for index in range(1, len(bars)):
            bar = bars[index]
            candidate_sar = sar + (acceleration_factor * (extreme_point - sar))
            if uptrend:
                if bar.low < candidate_sar:
                    uptrend = False
                    sar = extreme_point
                    extreme_point = bar.low
                    acceleration_factor = self.step
                else:
                    sar = min(candidate_sar, bars[index - 1].low, bar.low)
                    if bar.high > extreme_point:
                        extreme_point = bar.high
                        acceleration_factor = min(acceleration_factor + self.step, self.max_step)
            else:
                if bar.high > candidate_sar:
                    uptrend = True
                    sar = extreme_point
                    extreme_point = bar.high
                    acceleration_factor = self.step
                else:
                    sar = max(candidate_sar, bars[index - 1].high, bar.high)
                    if bar.low < extreme_point:
                        extreme_point = bar.low
                        acceleration_factor = min(acceleration_factor + self.step, self.max_step)
            outputs.extend(
                [
                    IndicatorOutput(
                        trade_date=bar.trade_date,
                        indicator_name=self.name,
                        component="sar",
                        parameter_signature=signature,
                        value=quantize_decimal(sar),
                    ),
                    IndicatorOutput(
                        trade_date=bar.trade_date,
                        indicator_name=self.name,
                        component="trend",
                        parameter_signature=signature,
                        value=Decimal("1") if uptrend else Decimal("-1"),
                    ),
                ]
            )
        return outputs
