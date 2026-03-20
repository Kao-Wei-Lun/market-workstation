from __future__ import annotations

from decimal import Decimal

from services.core.indicators.base import BarDataPoint, IndicatorOutput


class OBVIndicator:
    name = "obv"

    def compute(self, bars: list[BarDataPoint]) -> list[IndicatorOutput]:
        if not bars:
            return []
        outputs: list[IndicatorOutput] = []
        current_value = Decimal("0")
        previous_close = bars[0].close
        outputs.append(
            IndicatorOutput(
                trade_date=bars[0].trade_date,
                indicator_name=self.name,
                component="value",
                parameter_signature="",
                value=current_value,
            )
        )
        for bar in bars[1:]:
            if bar.close > previous_close:
                current_value += Decimal(bar.volume)
            elif bar.close < previous_close:
                current_value -= Decimal(bar.volume)
            previous_close = bar.close
            outputs.append(
                IndicatorOutput(
                    trade_date=bar.trade_date,
                    indicator_name=self.name,
                    component="value",
                    parameter_signature="",
                    value=current_value,
                )
            )
        return outputs
