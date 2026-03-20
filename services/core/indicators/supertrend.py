from __future__ import annotations

from decimal import Decimal

from services.core.indicators.atr import ATRIndicator
from services.core.indicators.base import BarDataPoint, IndicatorOutput
from services.core.indicators.utils import quantize_decimal


class SupertrendIndicator:
    name = "supertrend"

    def __init__(self, period: int = 10, multiplier: int = 3) -> None:
        self.period = period
        self.multiplier = multiplier

    def compute(self, bars: list[BarDataPoint]) -> list[IndicatorOutput]:
        atr_outputs = ATRIndicator(self.period).compute(bars)
        atr_map = {item.trade_date: item.value for item in atr_outputs}
        outputs: list[IndicatorOutput] = []
        signature = f"period={self.period},multiplier={self.multiplier}"
        previous_upper: Decimal | None = None
        previous_lower: Decimal | None = None
        previous_supertrend: Decimal | None = None
        previous_close: Decimal | None = None
        for bar in bars:
            atr = atr_map.get(bar.trade_date)
            if atr is None:
                continue
            hl2 = (bar.high + bar.low) / 2
            basic_upper = quantize_decimal(hl2 + (Decimal(self.multiplier) * atr))
            basic_lower = quantize_decimal(hl2 - (Decimal(self.multiplier) * atr))
            if previous_upper is None or previous_close is None:
                final_upper = basic_upper
                final_lower = basic_lower
            else:
                assert previous_lower is not None
                final_upper = (
                    basic_upper
                    if basic_upper < previous_upper or previous_close > previous_upper
                    else previous_upper
                )
                final_lower = (
                    basic_lower
                    if basic_lower > previous_lower or previous_close < previous_lower
                    else previous_lower
                )
            if previous_supertrend is None:
                supertrend = final_lower
            elif previous_supertrend == previous_upper:
                supertrend = final_upper if bar.close <= final_upper else final_lower
            else:
                supertrend = final_lower if bar.close >= final_lower else final_upper
            trend = Decimal("1") if bar.close >= supertrend else Decimal("-1")
            outputs.extend(
                [
                    IndicatorOutput(
                        trade_date=bar.trade_date,
                        indicator_name=self.name,
                        component="value",
                        parameter_signature=signature,
                        value=quantize_decimal(supertrend),
                    ),
                    IndicatorOutput(
                        trade_date=bar.trade_date,
                        indicator_name=self.name,
                        component="trend",
                        parameter_signature=signature,
                        value=trend,
                    ),
                ]
            )
            previous_upper = final_upper
            previous_lower = final_lower
            previous_supertrend = supertrend
            previous_close = bar.close
        return sorted(outputs, key=lambda item: (item.trade_date, item.component))
