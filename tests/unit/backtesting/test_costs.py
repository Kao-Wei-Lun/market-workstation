from decimal import Decimal

from services.core.backtesting.costs import calculate_trade_costs
from services.schemas.backtesting import CostModelDefinition


def test_cost_calculation_applies_fee_tax_and_slippage() -> None:
    result = calculate_trade_costs(
        price=Decimal("10"),
        quantity=100,
        costs=CostModelDefinition(
            fee_rate=Decimal("0.001"),
            tax_rate=Decimal("0.003"),
            slippage_rate=Decimal("0.0005"),
        ),
        is_exit=True,
    )

    assert result.fee == Decimal("1.000000")
    assert result.tax == Decimal("3.000000")
    assert result.slippage == Decimal("0.500000")
