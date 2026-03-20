from __future__ import annotations

from services.core.indicators.base import BarDataPoint, IndicatorOutput
from services.core.indicators.utils import quantize_decimal, rolling_max, rolling_min


class DonchianChannelIndicator:
    name = "donchian_channel"

    def __init__(self, period: int = 20) -> None:
        self.period = period

    def compute(self, bars: list[BarDataPoint]) -> list[IndicatorOutput]:
        highest_highs = rolling_max([bar.high for bar in bars], self.period)
        lowest_lows = rolling_min([bar.low for bar in bars], self.period)
        signature = f"period={self.period}"
        outputs: list[IndicatorOutput] = []
        for index, bar in enumerate(bars):
            highest = highest_highs[index]
            lowest = lowest_lows[index]
            if highest is None or lowest is None:
                continue
            middle = quantize_decimal((highest + lowest) / 2)
            outputs.extend(
                [
                    IndicatorOutput(
                        trade_date=bar.trade_date,
                        indicator_name=self.name,
                        component="upper_band",
                        parameter_signature=signature,
                        value=highest,
                    ),
                    IndicatorOutput(
                        trade_date=bar.trade_date,
                        indicator_name=self.name,
                        component="middle_band",
                        parameter_signature=signature,
                        value=middle,
                    ),
                    IndicatorOutput(
                        trade_date=bar.trade_date,
                        indicator_name=self.name,
                        component="lower_band",
                        parameter_signature=signature,
                        value=lowest,
                    ),
                ]
            )
        return outputs
