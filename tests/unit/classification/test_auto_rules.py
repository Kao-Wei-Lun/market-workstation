from __future__ import annotations

from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from services.core.classification.rules import (
    create_auto_classification_rule,
    evaluate_auto_classification_rules,
    list_auto_classification_rules,
    update_auto_classification_rule,
)
from services.core.classification.tags import add_tag_to_instrument, list_tags_for_instrument
from services.db.base import Base
from services.models import import_models
from services.models.instrument import Instrument
from services.schemas.classification import (
    AutoClassificationExpression,
    AutoClassificationRuleCreate,
    AutoClassificationRuleUpdate,
)


def _build_session() -> Session:
    import_models()
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return session_factory()


def test_auto_classification_rule_validation_rejects_invalid_operator() -> None:
    try:
        AutoClassificationExpression.model_validate(
            {
                "condition": {
                    "field": "market",
                    "operator": "contains",
                    "value": "TW",
                }
            }
        )
    except ValidationError as exc:
        assert "not supported" in str(exc)
    else:
        raise AssertionError("expected validation error")


def test_auto_classification_rule_evaluation_and_tag_application() -> None:
    session = _build_session()
    instruments = [
        Instrument(
            symbol="2330",
            name="TSMC",
            market="TW",
            asset_type="stock",
            currency="TWD",
            timezone="Asia/Taipei",
            source_route="twse_openapi",
        ),
        Instrument(
            symbol="QQQ",
            name="Nasdaq ETF",
            market="US",
            asset_type="etf",
            currency="USD",
            timezone="America/New_York",
            source_route="manual_csv",
        ),
    ]
    session.add_all(instruments)
    session.flush()
    add_tag_to_instrument(session, instrument_id=instruments[0].id, tag="sample")

    rule = create_auto_classification_rule(
        session,
        payload=AutoClassificationRuleCreate(
            name="tw sample instruments",
            target_tag="tw-core",
            definition=AutoClassificationExpression.model_validate(
                {
                    "all": [
                        {"condition": {"field": "market", "operator": "equals", "value": "TW"}},
                        {"condition": {"field": "tag", "operator": "has", "value": "sample"}},
                    ]
                }
            ),
        ),
    )
    update_auto_classification_rule(
        session,
        rule=rule,
        payload=AutoClassificationRuleUpdate(description="Taiwan sample bucket"),
    )

    result = evaluate_auto_classification_rules(session)

    assert result.rules_evaluated == 1
    assert result.instruments_evaluated == 2
    assert result.matches_found == 1
    assert result.tags_added == 1
    assert [tag.tag for tag in list_tags_for_instrument(session, instrument_id=instruments[0].id)] == [
        "sample",
        "tw-core",
    ]
    assert list_auto_classification_rules(session)[0].description == "Taiwan sample bucket"
