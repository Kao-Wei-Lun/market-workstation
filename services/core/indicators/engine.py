from __future__ import annotations

from collections.abc import Iterable

from services.core.indicators.base import BarDataPoint, IndicatorCalculator, IndicatorOutput


class IndicatorEngine:
    def __init__(self, calculators: Iterable[IndicatorCalculator]) -> None:
        self.calculators = list(calculators)

    def compute(self, bars: list[BarDataPoint]) -> list[IndicatorOutput]:
        outputs: list[IndicatorOutput] = []
        for calculator in self.calculators:
            outputs.extend(calculator.compute(bars))
        return sorted(outputs, key=lambda item: (item.trade_date, item.indicator_name, item.component))
