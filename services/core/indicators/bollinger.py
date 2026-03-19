from __future__ import annotations

from services.core.indicators.base import BarDataPoint, IndicatorOutput
from services.core.indicators.utils import decimal_mean, decimal_stddev, quantize_decimal


class BollingerBandsIndicator:
    name = "bollinger_bands"

    def __init__(self, period: int = 20, stddev_multiplier: int = 2) -> None:
        self.period = period
        self.stddev_multiplier = stddev_multiplier

    def compute(self, bars: list[BarDataPoint]) -> list[IndicatorOutput]:
        outputs: list[IndicatorOutput] = []
        signature = f"period={self.period},stddev_multiplier={self.stddev_multiplier}"
        for index in range(self.period - 1, len(bars)):
            window = [bar.close for bar in bars[index + 1 - self.period : index + 1]]
            middle = decimal_mean(window)
            standard_deviation = decimal_stddev(window)
            upper = middle + (standard_deviation * self.stddev_multiplier)
            lower = middle - (standard_deviation * self.stddev_multiplier)
            trade_date = bars[index].trade_date
            outputs.extend(
                [
                    IndicatorOutput(
                        trade_date=trade_date,
                        indicator_name=self.name,
                        component="middle_band",
                        parameter_signature=signature,
                        value=quantize_decimal(middle),
                    ),
                    IndicatorOutput(
                        trade_date=trade_date,
                        indicator_name=self.name,
                        component="upper_band",
                        parameter_signature=signature,
                        value=quantize_decimal(upper),
                    ),
                    IndicatorOutput(
                        trade_date=trade_date,
                        indicator_name=self.name,
                        component="lower_band",
                        parameter_signature=signature,
                        value=quantize_decimal(lower),
                    ),
                ]
            )
        return outputs
