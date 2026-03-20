from __future__ import annotations

from decimal import Decimal

from services.core.indicators.atr import ATRIndicator
from services.core.indicators.base import BarDataPoint, IndicatorOutput
from services.core.indicators.utils import ema_series, quantize_decimal


class KeltnerChannelIndicator:
    name = "keltner_channel"

    def __init__(self, ema_period: int = 20, atr_period: int = 10, multiplier: int = 2) -> None:
        self.ema_period = ema_period
        self.atr_period = atr_period
        self.multiplier = multiplier

    def compute(self, bars: list[BarDataPoint]) -> list[IndicatorOutput]:
        closes = [bar.close for bar in bars]
        ema_values = ema_series(closes, self.ema_period)
        atr_map = {item.trade_date: item.value for item in ATRIndicator(self.atr_period).compute(bars)}
        signature = (
            f"ema_period={self.ema_period},atr_period={self.atr_period},multiplier={self.multiplier}"
        )
        outputs: list[IndicatorOutput] = []
        for index, bar in enumerate(bars):
            ema_value = ema_values[index]
            atr_value = atr_map.get(bar.trade_date)
            if ema_value is None or atr_value is None:
                continue
            offset = Decimal(self.multiplier) * atr_value
            outputs.extend(
                [
                    IndicatorOutput(
                        trade_date=bar.trade_date,
                        indicator_name=self.name,
                        component="middle_band",
                        parameter_signature=signature,
                        value=ema_value,
                    ),
                    IndicatorOutput(
                        trade_date=bar.trade_date,
                        indicator_name=self.name,
                        component="upper_band",
                        parameter_signature=signature,
                        value=quantize_decimal(ema_value + offset),
                    ),
                    IndicatorOutput(
                        trade_date=bar.trade_date,
                        indicator_name=self.name,
                        component="lower_band",
                        parameter_signature=signature,
                        value=quantize_decimal(ema_value - offset),
                    ),
                ]
            )
        return sorted(outputs, key=lambda item: (item.trade_date, item.component))
