from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from services.core.backtesting.dsl import evaluate_rule, parse_strategy_definition


def test_strategy_definition_parses_richer_rule_tree_with_universe_filters() -> None:
    definition = {
        "instrument_id": 1,
        "position_size": Decimal("0.5"),
        "initial_cash": Decimal("10000"),
        "max_concurrent_positions": 2,
        "stop_loss_pct": Decimal("5"),
        "take_profit_pct": Decimal("10"),
        "time_exit_days": 4,
        "universe": {
            "required_tags": ["semiconductor", "growth"],
            "market": "TW",
        },
        "entry_rule": {
            "all": [
                {
                    "left": {"kind": "price", "field": "close"},
                    "operator": "gt",
                    "right": {
                        "kind": "indicator",
                        "indicator_name": "sma",
                        "component": "value",
                        "parameter_signature": "period=20",
                    },
                },
                {
                    "any": [
                        {
                            "left": {"kind": "indicator", "indicator_name": "rsi", "component": "value", "parameter_signature": "period=14"},
                            "operator": "lt",
                            "right": {"kind": "constant", "value": "40"},
                        },
                        {
                            "left": {"kind": "price", "field": "volume"},
                            "operator": "gt",
                            "right": {"kind": "parameter", "parameter_name": "volume_floor"},
                        },
                    ]
                },
            ]
        },
        "exit_rule": {
            "any": [
                {
                    "left": {"kind": "price", "field": "close"},
                    "operator": "lt",
                    "right": {
                        "kind": "indicator",
                        "indicator_name": "sma",
                        "component": "value",
                        "parameter_signature": "period=20",
                    },
                },
                {
                    "left": {"kind": "indicator", "indicator_name": "rsi", "component": "value", "parameter_signature": "period=14"},
                    "operator": "gt",
                    "right": {"kind": "constant", "value": "70"},
                },
            ]
        },
    }

    parsed = parse_strategy_definition(definition)

    assert parsed.max_concurrent_positions == 2
    assert parsed.universe is not None
    assert parsed.universe.required_tags == ["growth", "semiconductor"]
    assert parsed.entry_rule.all is not None


def test_evaluate_rule_supports_parameter_and_indicator_operands() -> None:
    rule = parse_strategy_definition(
        {
            "instrument_id": 1,
            "entry_rule": {
                "all": [
                    {
                        "left": {"kind": "price", "field": "close"},
                        "operator": "gt",
                        "right": {
                            "kind": "indicator",
                            "indicator_name": "sma",
                            "component": "value",
                            "parameter_signature": "period=20",
                        },
                    },
                    {
                        "left": {"kind": "price", "field": "volume"},
                        "operator": "gt",
                        "right": {"kind": "parameter", "parameter_name": "volume_floor"},
                    },
                ]
            },
            "exit_rule": {
                "left": {"kind": "price", "field": "close"},
                "operator": "lt",
                "right": {"kind": "constant", "value": "10"},
            },
        }
    ).entry_rule

    matched = evaluate_rule(
        rule,
        trade_date=date(2024, 1, 2),
        price_values={"close": Decimal("12"), "volume": Decimal("1500")},
        indicator_values={
            (date(2024, 1, 2), "sma", "value", "period=20"): Decimal("11")
        },
        parameters={"volume_floor": Decimal("1000")},
    )
    not_matched = evaluate_rule(
        rule,
        trade_date=date(2024, 1, 2),
        price_values={"close": Decimal("12"), "volume": Decimal("900")},
        indicator_values={
            (date(2024, 1, 2), "sma", "value", "period=20"): Decimal("11")
        },
        parameters={"volume_floor": Decimal("1000")},
    )

    assert matched is True
    assert not_matched is False


def test_strategy_definition_rejects_invalid_position_size() -> None:
    with pytest.raises(ValidationError):
        parse_strategy_definition(
            {
                "instrument_id": 1,
                "position_size": "0",
                "entry_rule": {
                    "left": {"kind": "price", "field": "close"},
                    "operator": "gt",
                    "right": {"kind": "constant", "value": "10"},
                },
                "exit_rule": {
                    "left": {"kind": "price", "field": "close"},
                    "operator": "lt",
                    "right": {"kind": "constant", "value": "9"},
                },
            }
        )
