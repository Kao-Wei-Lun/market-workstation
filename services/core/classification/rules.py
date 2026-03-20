from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy.orm import Session

from services.core.classification.tags import add_tag_to_instrument
from services.models.auto_classification_rule import AutoClassificationRule
from services.models.instrument import Instrument
from services.models.instrument_tag import InstrumentTag
from services.schemas.classification import (
    AutoClassificationExpression,
    AutoClassificationRuleCreate,
    AutoClassificationRuleUpdate,
)


@dataclass(frozen=True)
class AutoClassificationEvaluationResult:
    rules_evaluated: int
    instruments_evaluated: int
    matches_found: int
    tags_added: int


def list_auto_classification_rules(session: Session) -> list[AutoClassificationRule]:
    return session.query(AutoClassificationRule).order_by(AutoClassificationRule.name.asc()).all()


def get_auto_classification_rule(session: Session, *, rule_id: int) -> AutoClassificationRule | None:
    return session.query(AutoClassificationRule).filter(AutoClassificationRule.id == rule_id).one_or_none()


def create_auto_classification_rule(
    session: Session,
    *,
    payload: AutoClassificationRuleCreate,
) -> AutoClassificationRule:
    rule = AutoClassificationRule(
        name=payload.name.strip(),
        description=_normalize_optional_text(payload.description),
        target_tag=payload.target_tag.strip().lower(),
        definition_json=payload.definition.model_dump(mode="json"),
        is_active=payload.is_active,
    )
    session.add(rule)
    session.flush()
    return rule


def update_auto_classification_rule(
    session: Session,
    *,
    rule: AutoClassificationRule,
    payload: AutoClassificationRuleUpdate,
) -> AutoClassificationRule:
    if payload.name is not None:
        rule.name = payload.name.strip()
    if payload.description is not None:
        rule.description = _normalize_optional_text(payload.description)
    if payload.target_tag is not None:
        rule.target_tag = payload.target_tag.strip().lower()
    if payload.definition is not None:
        rule.definition_json = payload.definition.model_dump(mode="json")
    if payload.is_active is not None:
        rule.is_active = payload.is_active
    session.flush()
    return rule


def delete_auto_classification_rule(session: Session, *, rule: AutoClassificationRule) -> None:
    session.delete(rule)
    session.flush()


def evaluate_auto_classification_rules(
    session: Session,
    *,
    rule_id: int | None = None,
) -> AutoClassificationEvaluationResult:
    rules_query = session.query(AutoClassificationRule)
    if rule_id is not None:
        rules_query = rules_query.filter(AutoClassificationRule.id == rule_id)
    else:
        rules_query = rules_query.filter(AutoClassificationRule.is_active.is_(True))
    rules = rules_query.order_by(AutoClassificationRule.id.asc()).all()

    instruments = (
        session.query(Instrument)
        .filter(Instrument.is_active.is_(True))
        .order_by(Instrument.id.asc())
        .all()
    )
    existing_tags = _load_existing_tags(session)

    matches_found = 0
    tags_added = 0
    for rule in rules:
        expression = AutoClassificationExpression.model_validate(rule.definition_json)
        for instrument in instruments:
            instrument_tags = existing_tags[instrument.id]
            if not _evaluate_expression(expression, instrument=instrument, tags=instrument_tags):
                continue
            matches_found += 1
            if rule.target_tag not in instrument_tags:
                add_tag_to_instrument(
                    session,
                    instrument_id=instrument.id,
                    tag=rule.target_tag,
                )
                instrument_tags.add(rule.target_tag)
                tags_added += 1

    session.flush()
    return AutoClassificationEvaluationResult(
        rules_evaluated=len(rules),
        instruments_evaluated=len(instruments),
        matches_found=matches_found,
        tags_added=tags_added,
    )


def _load_existing_tags(session: Session) -> dict[int, set[str]]:
    tags_by_instrument: dict[int, set[str]] = defaultdict(set)
    for instrument_id, tag in session.query(InstrumentTag.instrument_id, InstrumentTag.tag).all():
        tags_by_instrument[instrument_id].add(tag)
    return tags_by_instrument


def _evaluate_expression(
    expression: AutoClassificationExpression,
    *,
    instrument: Instrument,
    tags: set[str],
) -> bool:
    if expression.condition is not None:
        return _evaluate_condition(
            field=expression.condition.field,
            operator=expression.condition.operator,
            value=expression.condition.value,
            instrument=instrument,
            tags=tags,
        )
    if expression.all is not None:
        return all(_evaluate_expression(item, instrument=instrument, tags=tags) for item in expression.all)
    if expression.any is not None:
        return any(_evaluate_expression(item, instrument=instrument, tags=tags) for item in expression.any)
    return False


def _evaluate_condition(
    *,
    field: str,
    operator: str,
    value: str,
    instrument: Instrument,
    tags: set[str],
) -> bool:
    normalized_value = value.strip().lower()
    if field == "tag":
        return normalized_value in tags

    instrument_value = getattr(instrument, field)
    normalized_field_value = str(instrument_value).strip().lower()
    if operator == "equals":
        return normalized_field_value == normalized_value
    if operator == "starts_with":
        return normalized_field_value.startswith(normalized_value)
    if operator == "ends_with":
        return normalized_field_value.endswith(normalized_value)
    if operator == "contains":
        return normalized_value in normalized_field_value
    return False


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None
