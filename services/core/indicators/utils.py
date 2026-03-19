from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from math import sqrt


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
