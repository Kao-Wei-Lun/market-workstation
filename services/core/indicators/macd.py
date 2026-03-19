from __future__ import annotations

from services.core.indicators.base import BarDataPoint, IndicatorOutput
from services.core.indicators.ema import EMAIndicator
from services.core.indicators.utils import quantize_decimal


class MACDIndicator:
    name = "macd"

    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> None:
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period

    def compute(self, bars: list[BarDataPoint]) -> list[IndicatorOutput]:
        fast_values = EMAIndicator(self.fast_period).compute(bars)
        slow_values = EMAIndicator(self.slow_period).compute(bars)
        fast_map = {item.trade_date: item.value for item in fast_values}
        slow_map = {item.trade_date: item.value for item in slow_values}
        shared_dates = [bar.trade_date for bar in bars if bar.trade_date in fast_map and bar.trade_date in slow_map]
        macd_line = [
            IndicatorOutput(
                trade_date=trade_date,
                indicator_name=self.name,
                component="macd_line",
                parameter_signature=self._signature,
                value=quantize_decimal(fast_map[trade_date] - slow_map[trade_date]),
            )
            for trade_date in shared_dates
        ]

        signal_inputs = [
            BarDataPoint(
                trade_date=item.trade_date,
                close=item.value,
                high=item.value,
                low=item.value,
                volume=0,
            )
            for item in macd_line
        ]
        signal_values = EMAIndicator(self.signal_period).compute(signal_inputs)
        signal_map = {item.trade_date: item.value for item in signal_values}

        outputs = list(macd_line)
        for item in signal_values:
            outputs.append(
                IndicatorOutput(
                    trade_date=item.trade_date,
                    indicator_name=self.name,
                    component="signal_line",
                    parameter_signature=self._signature,
                    value=item.value,
                )
            )
        for item in macd_line:
            if item.trade_date in signal_map:
                outputs.append(
                    IndicatorOutput(
                        trade_date=item.trade_date,
                        indicator_name=self.name,
                        component="histogram",
                        parameter_signature=self._signature,
                        value=quantize_decimal(item.value - signal_map[item.trade_date]),
                    )
                )
        return sorted(outputs, key=lambda item: (item.trade_date, item.component))

    @property
    def _signature(self) -> str:
        return (
            f"fast_period={self.fast_period},"
            f"slow_period={self.slow_period},"
            f"signal_period={self.signal_period}"
        )
