from __future__ import annotations

from decimal import Decimal

from services.core.indicators.base import BarDataPoint, IndicatorOutput
from services.core.indicators.utils import quantize_decimal


class MFIIndicator:
    name = "mfi"

    def __init__(self, period: int = 14) -> None:
        self.period = period

    def compute(self, bars: list[BarDataPoint]) -> list[IndicatorOutput]:
        if len(bars) <= self.period:
            return []
        typical_prices = [(bar.high + bar.low + bar.close) / 3 for bar in bars]
        positive_flow = [Decimal("0")]
        negative_flow = [Decimal("0")]
        for index in range(1, len(bars)):
            raw_money_flow = typical_prices[index] * Decimal(bars[index].volume)
            if typical_prices[index] > typical_prices[index - 1]:
                positive_flow.append(raw_money_flow)
                negative_flow.append(Decimal("0"))
            elif typical_prices[index] < typical_prices[index - 1]:
                positive_flow.append(Decimal("0"))
                negative_flow.append(raw_money_flow)
            else:
                positive_flow.append(Decimal("0"))
                negative_flow.append(Decimal("0"))
        outputs: list[IndicatorOutput] = []
        signature = f"period={self.period}"
        for index in range(self.period, len(bars)):
            positive_sum = sum(positive_flow[index + 1 - self.period : index + 1], Decimal("0"))
            negative_sum = sum(negative_flow[index + 1 - self.period : index + 1], Decimal("0"))
            if negative_sum == 0:
                mfi = Decimal("100")
            else:
                money_ratio = positive_sum / negative_sum
                mfi = Decimal("100") - (Decimal("100") / (Decimal("1") + money_ratio))
            outputs.append(
                IndicatorOutput(
                    trade_date=bars[index].trade_date,
                    indicator_name=self.name,
                    component="value",
                    parameter_signature=signature,
                    value=quantize_decimal(mfi),
                )
            )
        return outputs
