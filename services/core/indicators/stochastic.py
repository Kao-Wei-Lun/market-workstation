from __future__ import annotations

from decimal import Decimal

from services.core.indicators.base import BarDataPoint, IndicatorOutput
from services.core.indicators.utils import quantize_decimal, rolling_max, rolling_min, sma_series


class StochasticIndicator:
    name = "stochastic"

    def __init__(self, k_period: int = 14, d_period: int = 3) -> None:
        self.k_period = k_period
        self.d_period = d_period

    def compute(self, bars: list[BarDataPoint]) -> list[IndicatorOutput]:
        highs = [bar.high for bar in bars]
        lows = [bar.low for bar in bars]
        highest_highs = rolling_max(highs, self.k_period)
        lowest_lows = rolling_min(lows, self.k_period)
        k_values: list[Decimal] = []
        k_index_map: list[int] = []
        outputs: list[IndicatorOutput] = []
        signature = f"k_period={self.k_period},d_period={self.d_period}"
        for index, bar in enumerate(bars):
            highest = highest_highs[index]
            lowest = lowest_lows[index]
            if highest is None or lowest is None:
                continue
            denominator = highest - lowest
            percent_k = Decimal("0") if denominator == 0 else quantize_decimal(((bar.close - lowest) / denominator) * Decimal("100"))
            k_values.append(percent_k)
            k_index_map.append(index)
            outputs.append(
                IndicatorOutput(
                    trade_date=bar.trade_date,
                    indicator_name=self.name,
                    component="percent_k",
                    parameter_signature=signature,
                    value=percent_k,
                )
            )
        d_values = sma_series(k_values, self.d_period)
        for idx, percent_d in enumerate(d_values):
            if percent_d is None:
                continue
            bar_index = k_index_map[idx]
            outputs.append(
                IndicatorOutput(
                    trade_date=bars[bar_index].trade_date,
                    indicator_name=self.name,
                    component="percent_d",
                    parameter_signature=signature,
                    value=percent_d,
                )
            )
        return sorted(outputs, key=lambda item: (item.trade_date, item.component))
