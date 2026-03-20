from __future__ import annotations

from decimal import Decimal

from services.core.indicators.base import BarDataPoint, IndicatorOutput
from services.core.indicators.utils import quantize_decimal, true_range_series, wilder_smoothing


class ADXIndicator:
    name = "adx"

    def __init__(self, period: int = 14) -> None:
        self.period = period

    def compute(self, bars: list[BarDataPoint]) -> list[IndicatorOutput]:
        if len(bars) <= self.period:
            return []

        plus_dm = [Decimal("0")]
        minus_dm = [Decimal("0")]
        for previous, current in zip(bars, bars[1:]):
            up_move = current.high - previous.high
            down_move = previous.low - current.low
            plus_dm.append(up_move if up_move > down_move and up_move > 0 else Decimal("0"))
            minus_dm.append(down_move if down_move > up_move and down_move > 0 else Decimal("0"))

        tr_smoothed = wilder_smoothing(true_range_series(bars), self.period)
        plus_smoothed = wilder_smoothing(plus_dm, self.period)
        minus_smoothed = wilder_smoothing(minus_dm, self.period)

        dx_values: list[Decimal | None] = [None] * len(bars)
        outputs: list[IndicatorOutput] = []
        signature = f"period={self.period}"
        for index in range(len(bars)):
            tr_value = tr_smoothed[index]
            plus_value = plus_smoothed[index]
            minus_value = minus_smoothed[index]
            if tr_value is None or plus_value is None or minus_value is None or tr_value == 0:
                continue
            plus_di = quantize_decimal((plus_value / tr_value) * Decimal("100"))
            minus_di = quantize_decimal((minus_value / tr_value) * Decimal("100"))
            di_sum = plus_di + minus_di
            dx = Decimal("0") if di_sum == 0 else quantize_decimal((abs(plus_di - minus_di) / di_sum) * Decimal("100"))
            dx_values[index] = dx
            outputs.extend(
                [
                    IndicatorOutput(
                        trade_date=bars[index].trade_date,
                        indicator_name=self.name,
                        component="plus_di",
                        parameter_signature=signature,
                        value=plus_di,
                    ),
                    IndicatorOutput(
                        trade_date=bars[index].trade_date,
                        indicator_name=self.name,
                        component="minus_di",
                        parameter_signature=signature,
                        value=minus_di,
                    ),
                ]
            )

        adx_seed_index = (self.period * 2) - 2
        if adx_seed_index >= len(bars):
            return sorted(outputs, key=lambda item: (item.trade_date, item.component))
        initial_dx = [value for value in dx_values[self.period - 1 : adx_seed_index + 1] if value is not None]
        if len(initial_dx) < self.period:
            return sorted(outputs, key=lambda item: (item.trade_date, item.component))
        previous_adx: Decimal = quantize_decimal(sum(initial_dx, Decimal("0")) / Decimal(self.period))
        outputs.append(
            IndicatorOutput(
                trade_date=bars[adx_seed_index].trade_date,
                indicator_name=self.name,
                component="adx",
                parameter_signature=signature,
                value=previous_adx,
            )
        )
        for index in range(adx_seed_index + 1, len(bars)):
            dx_value = dx_values[index]
            if dx_value is None:
                continue
            previous_adx = quantize_decimal(
                ((previous_adx * Decimal(self.period - 1)) + dx_value) / Decimal(self.period)
            )
            outputs.append(
                IndicatorOutput(
                    trade_date=bars[index].trade_date,
                    indicator_name=self.name,
                    component="adx",
                    parameter_signature=signature,
                    value=previous_adx,
                )
            )
        return sorted(outputs, key=lambda item: (item.trade_date, item.component))
