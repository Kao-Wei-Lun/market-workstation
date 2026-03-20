from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from math import sqrt

from services.core.indicators.base import BarDataPoint


def quantize_decimal(value: Decimal, scale: str = "0.000001") -> Decimal:
    return value.quantize(Decimal(scale), rounding=ROUND_HALF_UP)


def decimal_mean(values: list[Decimal]) -> Decimal:
    return sum(values, Decimal("0")) / Decimal(len(values))


def decimal_stddev(values: list[Decimal]) -> Decimal:
    if not values:
        return Decimal("0")
    mean = decimal_mean(values)
    variance = sum((value - mean) ** 2 for value in values) / Decimal(len(values))
    return Decimal(str(sqrt(float(variance))))


def ema_series(values: list[Decimal], period: int) -> list[Decimal | None]:
    if len(values) < period:
        return [None] * len(values)
    multiplier = Decimal("2") / Decimal(period + 1)
    seed = decimal_mean(values[:period])
    outputs: list[Decimal | None] = [None] * len(values)
    outputs[period - 1] = quantize_decimal(seed)
    previous = seed
    for index in range(period, len(values)):
        previous = ((values[index] - previous) * multiplier) + previous
        outputs[index] = quantize_decimal(previous)
    return outputs


def sma_series(values: list[Decimal], period: int) -> list[Decimal | None]:
    if period <= 0:
        raise ValueError("period must be positive")
    outputs: list[Decimal | None] = [None] * len(values)
    for index in range(period - 1, len(values)):
        window = values[index + 1 - period : index + 1]
        outputs[index] = quantize_decimal(decimal_mean(window))
    return outputs


def wilder_smoothing(values: list[Decimal], period: int) -> list[Decimal | None]:
    if len(values) < period:
        return [None] * len(values)
    outputs: list[Decimal | None] = [None] * len(values)
    initial = sum(values[:period], Decimal("0"))
    outputs[period - 1] = quantize_decimal(initial)
    previous = initial
    for index in range(period, len(values)):
        previous = previous - (previous / Decimal(period)) + values[index]
        outputs[index] = quantize_decimal(previous)
    return outputs


def rolling_max(values: list[Decimal], period: int) -> list[Decimal | None]:
    outputs: list[Decimal | None] = [None] * len(values)
    for index in range(period - 1, len(values)):
        outputs[index] = max(values[index + 1 - period : index + 1])
    return outputs


def rolling_min(values: list[Decimal], period: int) -> list[Decimal | None]:
    outputs: list[Decimal | None] = [None] * len(values)
    for index in range(period - 1, len(values)):
        outputs[index] = min(values[index + 1 - period : index + 1])
    return outputs


def true_range_series(bars: list[BarDataPoint]) -> list[Decimal]:
    if not bars:
        return []
    outputs: list[Decimal] = []
    previous_close: Decimal | None = None
    for bar in bars:
        if previous_close is None:
            outputs.append(bar.high - bar.low)
        else:
            outputs.append(
                max(
                    bar.high - bar.low,
                    abs(bar.high - previous_close),
                    abs(bar.low - previous_close),
                )
            )
        previous_close = bar.close
    return outputs
