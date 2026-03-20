from __future__ import annotations

from services.core.indicators.base import BarDataPoint, IndicatorOutput
from services.core.indicators.utils import quantize_decimal, rolling_max, rolling_min


class IchimokuIndicator:
    name = "ichimoku"

    def __init__(self, conversion_period: int = 9, base_period: int = 26, span_b_period: int = 52) -> None:
        self.conversion_period = conversion_period
        self.base_period = base_period
        self.span_b_period = span_b_period

    def compute(self, bars: list[BarDataPoint]) -> list[IndicatorOutput]:
        highs = [bar.high for bar in bars]
        lows = [bar.low for bar in bars]
        conversion_high = rolling_max(highs, self.conversion_period)
        conversion_low = rolling_min(lows, self.conversion_period)
        base_high = rolling_max(highs, self.base_period)
        base_low = rolling_min(lows, self.base_period)
        span_b_high = rolling_max(highs, self.span_b_period)
        span_b_low = rolling_min(lows, self.span_b_period)
        signature = (
            f"conversion_period={self.conversion_period},"
            f"base_period={self.base_period},"
            f"span_b_period={self.span_b_period}"
        )
        outputs: list[IndicatorOutput] = []
        for index, bar in enumerate(bars):
            conversion_high_value = conversion_high[index]
            conversion_low_value = conversion_low[index]
            if conversion_high_value is not None and conversion_low_value is not None:
                conversion = quantize_decimal((conversion_high_value + conversion_low_value) / 2)
                outputs.append(
                    IndicatorOutput(
                        trade_date=bar.trade_date,
                        indicator_name=self.name,
                        component="conversion_line",
                        parameter_signature=signature,
                        value=conversion,
                    )
                )
            else:
                conversion = None
            base_high_value = base_high[index]
            base_low_value = base_low[index]
            if base_high_value is not None and base_low_value is not None:
                base = quantize_decimal((base_high_value + base_low_value) / 2)
                outputs.append(
                    IndicatorOutput(
                        trade_date=bar.trade_date,
                        indicator_name=self.name,
                        component="base_line",
                        parameter_signature=signature,
                        value=base,
                    )
                )
            else:
                base = None
            if conversion is not None and base is not None:
                outputs.append(
                    IndicatorOutput(
                        trade_date=bar.trade_date,
                        indicator_name=self.name,
                        component="leading_span_a",
                        parameter_signature=signature,
                        value=quantize_decimal((conversion + base) / 2),
                    )
                )
            span_b_high_value = span_b_high[index]
            span_b_low_value = span_b_low[index]
            if span_b_high_value is not None and span_b_low_value is not None:
                outputs.append(
                    IndicatorOutput(
                        trade_date=bar.trade_date,
                        indicator_name=self.name,
                        component="leading_span_b",
                        parameter_signature=signature,
                        value=quantize_decimal((span_b_high_value + span_b_low_value) / 2),
                    )
                )
            outputs.append(
                IndicatorOutput(
                    trade_date=bar.trade_date,
                    indicator_name=self.name,
                    component="lagging_span",
                    parameter_signature=signature,
                    value=bar.close,
                )
            )
        return sorted(outputs, key=lambda item: (item.trade_date, item.component))
