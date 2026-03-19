from __future__ import annotations

from datetime import date
from decimal import Decimal

from services.schemas.backtesting import OperandDefinition, RuleDefinition, StrategyDefinition


def evaluate_rule(
    rule: RuleDefinition,
    *,
    trade_date: date,
    price_values: dict[str, Decimal],
    indicator_values: dict[tuple[date, str, str, str], Decimal],
) -> bool:
    if rule.all is not None:
        return all(
            evaluate_rule(
                child,
                trade_date=trade_date,
                price_values=price_values,
                indicator_values=indicator_values,
            )
            for child in rule.all
        )
    if rule.any is not None:
        return any(
            evaluate_rule(
                child,
                trade_date=trade_date,
                price_values=price_values,
                indicator_values=indicator_values,
            )
            for child in rule.any
        )

    left = resolve_operand(
        rule.left,
        trade_date=trade_date,
        price_values=price_values,
        indicator_values=indicator_values,
    )
    right = resolve_operand(
        rule.right,
        trade_date=trade_date,
        price_values=price_values,
        indicator_values=indicator_values,
    )
    if left is None or right is None or rule.operator is None:
        return False
    return _compare(left, right, rule.operator)


def resolve_operand(
    operand: OperandDefinition | None,
    *,
    trade_date: date,
    price_values: dict[str, Decimal],
    indicator_values: dict[tuple[date, str, str, str], Decimal],
) -> Decimal | None:
    if operand is None:
        return None
    if operand.kind == "price":
        return price_values.get(operand.field or "")
    if operand.kind == "constant":
        return operand.value
    if operand.kind == "indicator":
        key = (
            trade_date,
            operand.indicator_name or "",
            operand.component or "",
            operand.parameter_signature or "",
        )
        return indicator_values.get(key)
    return None


def parse_strategy_definition(definition: dict) -> StrategyDefinition:
    return StrategyDefinition.model_validate(definition)


def _compare(left: Decimal, right: Decimal, operator: str) -> bool:
    if operator == "gt":
        return left > right
    if operator == "gte":
        return left >= right
    if operator == "lt":
        return left < right
    if operator == "lte":
        return left <= right
    if operator == "eq":
        return left == right
    if operator == "neq":
        return left != right
    raise ValueError(f"unsupported operator: {operator}")
