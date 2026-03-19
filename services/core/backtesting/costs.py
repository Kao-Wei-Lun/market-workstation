from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from services.schemas.backtesting import CostModelDefinition


@dataclass(frozen=True)
class CostBreakdown:
    fee: Decimal
    tax: Decimal
    slippage: Decimal


def calculate_trade_costs(
    *,
    price: Decimal,
    quantity: int,
    costs: CostModelDefinition,
    is_exit: bool,
) -> CostBreakdown:
    notional = price * quantity
    fee = _q(notional * costs.fee_rate)
    tax = _q(notional * costs.tax_rate) if is_exit else Decimal("0")
    slippage = _q(notional * costs.slippage_rate)
    return CostBreakdown(fee=fee, tax=tax, slippage=slippage)


def apply_entry_slippage(price: Decimal, slippage_rate: Decimal) -> Decimal:
    return _q(price * (Decimal("1") + slippage_rate))


def apply_exit_slippage(price: Decimal, slippage_rate: Decimal) -> Decimal:
    return _q(price * (Decimal("1") - slippage_rate))


def _q(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
