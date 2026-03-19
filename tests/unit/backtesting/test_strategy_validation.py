from decimal import Decimal

import pytest
from pydantic import ValidationError

from services.core.backtesting.dsl import parse_strategy_definition


def test_strategy_definition_parses_valid_rule_tree() -> None:
    definition = {
        "instrument_id": 1,
        "position_size": Decimal("1"),
        "initial_cash": Decimal("10000"),
        "entry_rule": {
            "left": {"kind": "price", "field": "close"},
            "operator": "gt",
            "right": {"kind": "constant", "value": "10"},
        },
        "exit_rule": {
            "left": {"kind": "indicator", "indicator_name": "sma", "component": "value", "parameter_signature": "period=3"},
            "operator": "lt",
            "right": {"kind": "price", "field": "close"},
        },
    }

    parsed = parse_strategy_definition(definition)

    assert parsed.instrument_id == 1
    assert parsed.entry_rule.operator == "gt"


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
