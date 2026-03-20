from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from services.core.exports import rows_to_csv
from services.core.classification.rules import (
    create_auto_classification_rule,
    delete_auto_classification_rule,
    evaluate_auto_classification_rules,
    get_auto_classification_rule,
    list_auto_classification_rules,
    update_auto_classification_rule,
)
from services.core.classification.scanner import scan_tag_group, scan_watchlist_group
from services.core.classification.summary import summarize_scanner_scope, summarize_tag_group, summarize_watchlist_group
from services.core.classification.tags import add_tag_to_instrument, list_tags_for_instrument, remove_tag_from_instrument
from services.core.classification.watchlists import (
    add_instrument_to_watchlist,
    create_watchlist,
    get_watchlist,
    list_watchlists,
    list_watchlist_items,
    remove_instrument_from_watchlist,
)
from services.db.session import get_db_session
from services.models.auto_classification_rule import AutoClassificationRule
from services.schemas.classification import (
    AutoClassificationExpression,
    AutoClassificationRuleCreate,
    AutoClassificationRuleEvaluationRead,
    AutoClassificationRuleEvaluationRequest,
    AutoClassificationRuleRead,
    AutoClassificationRuleUpdate,
    GroupScannerRead,
    GroupScannerRequest,
    GroupSummaryRead,
    InstrumentTagCreate,
    InstrumentTagRead,
    WatchlistCreate,
    WatchlistItemRead,
    WatchlistRead,
)
from services.schemas.output import WatchlistSummarySnapshotRead

router = APIRouter(tags=["classification"])


def _serialize_rule(rule: AutoClassificationRule) -> AutoClassificationRuleRead:
    return AutoClassificationRuleRead(
        id=rule.id,
        name=rule.name,
        description=rule.description,
        target_tag=rule.target_tag,
        definition=AutoClassificationExpression.model_validate(rule.definition_json),
        is_active=rule.is_active,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


@router.post("/instruments/{instrument_id}/tags", response_model=InstrumentTagRead)
async def create_instrument_tag(
    instrument_id: int,
    payload: InstrumentTagCreate,
    session: Session = Depends(get_db_session),
) -> InstrumentTagRead:
    tag = add_tag_to_instrument(session, instrument_id=instrument_id, tag=payload.tag)
    session.commit()
    return InstrumentTagRead.model_validate(tag)


@router.get("/instruments/{instrument_id}/tags", response_model=list[InstrumentTagRead])
async def get_instrument_tags(
    instrument_id: int,
    session: Session = Depends(get_db_session),
) -> list[InstrumentTagRead]:
    tags = list_tags_for_instrument(session, instrument_id=instrument_id)
    return [InstrumentTagRead.model_validate(tag) for tag in tags]


@router.delete("/instruments/{instrument_id}/tags/{tag}")
async def delete_instrument_tag(
    instrument_id: int,
    tag: str,
    session: Session = Depends(get_db_session),
) -> dict[str, bool]:
    removed = remove_tag_from_instrument(session, instrument_id=instrument_id, tag=tag)
    if not removed:
        raise HTTPException(status_code=404, detail="tag not found")
    session.commit()
    return {"removed": True}


@router.post("/watchlists", response_model=WatchlistRead)
async def create_watchlist_route(
    payload: WatchlistCreate,
    session: Session = Depends(get_db_session),
) -> WatchlistRead:
    watchlist = create_watchlist(session, name=payload.name, description=payload.description)
    session.commit()
    return WatchlistRead.model_validate(watchlist)


@router.get("/watchlists", response_model=list[WatchlistRead])
async def list_watchlists_route(
    session: Session = Depends(get_db_session),
) -> list[WatchlistRead]:
    return [WatchlistRead.model_validate(item) for item in list_watchlists(session)]


@router.post("/watchlists/{watchlist_id}/items/{instrument_id}", response_model=WatchlistItemRead)
async def add_watchlist_item_route(
    watchlist_id: int,
    instrument_id: int,
    session: Session = Depends(get_db_session),
) -> WatchlistItemRead:
    if get_watchlist(session, watchlist_id=watchlist_id) is None:
        raise HTTPException(status_code=404, detail="watchlist not found")
    item = add_instrument_to_watchlist(session, watchlist_id=watchlist_id, instrument_id=instrument_id)
    session.commit()
    return WatchlistItemRead.model_validate(item)


@router.delete("/watchlists/{watchlist_id}/items/{instrument_id}")
async def delete_watchlist_item_route(
    watchlist_id: int,
    instrument_id: int,
    session: Session = Depends(get_db_session),
) -> dict[str, bool]:
    removed = remove_instrument_from_watchlist(
        session,
        watchlist_id=watchlist_id,
        instrument_id=instrument_id,
    )
    if not removed:
        raise HTTPException(status_code=404, detail="watchlist item not found")
    session.commit()
    return {"removed": True}


@router.get("/classification-rules", response_model=list[AutoClassificationRuleRead])
async def list_auto_classification_rules_route(
    session: Session = Depends(get_db_session),
) -> list[AutoClassificationRuleRead]:
    rules = list_auto_classification_rules(session)
    return [_serialize_rule(rule) for rule in rules]


@router.post("/classification-rules", response_model=AutoClassificationRuleRead)
async def create_auto_classification_rule_route(
    payload: AutoClassificationRuleCreate,
    session: Session = Depends(get_db_session),
) -> AutoClassificationRuleRead:
    rule = create_auto_classification_rule(session, payload=payload)
    session.commit()
    return _serialize_rule(rule)


@router.put("/classification-rules/{rule_id}", response_model=AutoClassificationRuleRead)
async def update_auto_classification_rule_route(
    rule_id: int,
    payload: AutoClassificationRuleUpdate,
    session: Session = Depends(get_db_session),
) -> AutoClassificationRuleRead:
    rule = get_auto_classification_rule(session, rule_id=rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="classification rule not found")
    updated_rule = update_auto_classification_rule(session, rule=rule, payload=payload)
    session.commit()
    return _serialize_rule(updated_rule)


@router.delete("/classification-rules/{rule_id}")
async def delete_auto_classification_rule_route(
    rule_id: int,
    session: Session = Depends(get_db_session),
) -> dict[str, bool]:
    rule = get_auto_classification_rule(session, rule_id=rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="classification rule not found")
    delete_auto_classification_rule(session, rule=rule)
    session.commit()
    return {"removed": True}


@router.post("/classification-rules/evaluate", response_model=AutoClassificationRuleEvaluationRead)
async def evaluate_auto_classification_rules_route(
    payload: AutoClassificationRuleEvaluationRequest,
    session: Session = Depends(get_db_session),
) -> AutoClassificationRuleEvaluationRead:
    if payload.rule_id is not None and get_auto_classification_rule(session, rule_id=payload.rule_id) is None:
        raise HTTPException(status_code=404, detail="classification rule not found")
    result = evaluate_auto_classification_rules(session, rule_id=payload.rule_id)
    session.commit()
    return AutoClassificationRuleEvaluationRead(**result.__dict__)


@router.get("/watchlists/{watchlist_id}/items", response_model=list[WatchlistItemRead])
async def get_watchlist_items_route(
    watchlist_id: int,
    session: Session = Depends(get_db_session),
) -> list[WatchlistItemRead]:
    if get_watchlist(session, watchlist_id=watchlist_id) is None:
        raise HTTPException(status_code=404, detail="watchlist not found")
    items = list_watchlist_items(session, watchlist_id=watchlist_id)
    return [WatchlistItemRead.model_validate(item) for item in items]


@router.get("/tags/{tag}/summary", response_model=GroupSummaryRead)
async def get_tag_summary_route(
    tag: str,
    trade_date: date,
    session: Session = Depends(get_db_session),
) -> GroupSummaryRead:
    return summarize_tag_group(session, tag=tag, trade_date=trade_date)


@router.get("/watchlists/{watchlist_id}/summary", response_model=GroupSummaryRead)
async def get_watchlist_summary_route(
    watchlist_id: int,
    trade_date: date,
    session: Session = Depends(get_db_session),
) -> GroupSummaryRead:
    if get_watchlist(session, watchlist_id=watchlist_id) is None:
        raise HTTPException(status_code=404, detail="watchlist not found")
    return summarize_watchlist_group(session, watchlist_id=watchlist_id, trade_date=trade_date)


@router.get("/watchlists/latest-summary", response_model=list[WatchlistSummarySnapshotRead])
async def list_latest_watchlist_summaries_route(
    trade_date: date,
    session: Session = Depends(get_db_session),
) -> list[WatchlistSummarySnapshotRead]:
    snapshots: list[WatchlistSummarySnapshotRead] = []
    for watchlist in list_watchlists(session):
        snapshots.append(
            WatchlistSummarySnapshotRead(
                watchlist=WatchlistRead.model_validate(watchlist),
                trade_date=trade_date,
                summary=summarize_watchlist_group(session, watchlist_id=watchlist.id, trade_date=trade_date),
            )
        )
    return snapshots


@router.get("/scanner/summary", response_model=GroupSummaryRead)
async def get_scanner_summary_route(
    trade_date: date,
    tag: str | None = None,
    watchlist_id: int | None = None,
    sma_parameter_signature: str = "period=20",
    session: Session = Depends(get_db_session),
) -> GroupSummaryRead:
    if tag is None and watchlist_id is None:
        raise HTTPException(status_code=422, detail="tag or watchlist_id is required")
    if watchlist_id is not None and get_watchlist(session, watchlist_id=watchlist_id) is None:
        raise HTTPException(status_code=404, detail="watchlist not found")
    return summarize_scanner_scope(
        session,
        trade_date=trade_date,
        tag=tag,
        watchlist_id=watchlist_id,
        sma_parameter_signature=sma_parameter_signature,
    )


@router.post("/scanner/run", response_model=GroupScannerRead)
async def run_group_scanner_route(
    payload: GroupScannerRequest,
    session: Session = Depends(get_db_session),
) -> GroupScannerRead:
    if payload.tag is not None:
        return scan_tag_group(
            session,
            tag=payload.tag,
            trade_date=payload.trade_date,
            sma_parameter_signature=payload.sma_parameter_signature,
            volume_lookback_days=payload.volume_lookback_days,
            flag_conditions=payload.flag_conditions,
        )

    watchlist_id = payload.watchlist_id
    if watchlist_id is None:
        raise HTTPException(status_code=422, detail="watchlist_id is required when tag is not provided")
    if get_watchlist(session, watchlist_id=watchlist_id) is None:
        raise HTTPException(status_code=404, detail="watchlist not found")
    return scan_watchlist_group(
        session,
        watchlist_id=watchlist_id,
        trade_date=payload.trade_date,
        sma_parameter_signature=payload.sma_parameter_signature,
        volume_lookback_days=payload.volume_lookback_days,
        flag_conditions=payload.flag_conditions,
    )


@router.get("/scanner/export")
async def export_group_scanner_route(
    trade_date: date,
    tag: str | None = None,
    watchlist_id: int | None = None,
    export_format: Literal["json", "csv"] = Query(default="json"),
    session: Session = Depends(get_db_session),
) -> Response:
    if tag is None and watchlist_id is None:
        raise HTTPException(status_code=422, detail="tag or watchlist_id is required")
    if watchlist_id is not None and get_watchlist(session, watchlist_id=watchlist_id) is None:
        raise HTTPException(status_code=404, detail="watchlist not found")
    summary = summarize_scanner_scope(session, trade_date=trade_date, tag=tag, watchlist_id=watchlist_id)
    if export_format == "json":
        return Response(content=summary.model_dump_json(indent=2), media_type="application/json")
    rows = [
        {
            "scope": tag or f"watchlist:{watchlist_id}",
            "trade_date": trade_date.isoformat(),
            "member_count": summary.member_count,
            "average_close_change_pct": str(summary.average_close_change_pct),
            "percentage_above_sma": str(summary.percentage_above_sma),
            "top_gainers": [item.symbol for item in summary.top_gainers],
            "top_losers": [item.symbol for item in summary.top_losers],
        }
    ]
    return Response(content=rows_to_csv(rows), media_type="text/csv")
