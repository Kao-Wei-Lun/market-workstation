from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from services.models.daily_bar import DailyBar
from services.models.indicator_value import IndicatorValue
from services.models.instrument import Instrument
from services.models.instrument_tag import InstrumentTag
from services.models.watchlist_item import WatchlistItem
from services.schemas.classification import GroupMemberChange, GroupSummaryRead


def summarize_tag_group(
    session: Session,
    *,
    tag: str,
    trade_date: date,
    sma_parameter_signature: str = "period=20",
) -> GroupSummaryRead:
    instrument_ids = [
        row.instrument_id
        for row in session.query(InstrumentTag.instrument_id)
        .filter(InstrumentTag.tag == tag.strip().lower())
        .all()
    ]
    return _build_group_summary(
        session,
        instrument_ids=instrument_ids,
        trade_date=trade_date,
        sma_parameter_signature=sma_parameter_signature,
    )


def summarize_watchlist_group(
    session: Session,
    *,
    watchlist_id: int,
    trade_date: date,
    sma_parameter_signature: str = "period=20",
) -> GroupSummaryRead:
    instrument_ids = [
        row.instrument_id
        for row in session.query(WatchlistItem.instrument_id)
        .filter(WatchlistItem.watchlist_id == watchlist_id)
        .all()
    ]
    return _build_group_summary(
        session,
        instrument_ids=instrument_ids,
        trade_date=trade_date,
        sma_parameter_signature=sma_parameter_signature,
    )


def _build_group_summary(
    session: Session,
    *,
    instrument_ids: list[int],
    trade_date: date,
    sma_parameter_signature: str,
) -> GroupSummaryRead:
    if not instrument_ids:
        return GroupSummaryRead(
            member_count=0,
            average_close_change_pct=Decimal("0"),
            top_gainers=[],
            top_losers=[],
            percentage_above_sma=Decimal("0"),
        )

    instruments = {
        instrument.id: instrument
        for instrument in session.query(Instrument).filter(Instrument.id.in_(instrument_ids)).all()
    }
    bars = (
        session.query(DailyBar)
        .filter(DailyBar.instrument_id.in_(instrument_ids), DailyBar.trade_date == trade_date)
        .all()
    )
    bar_map = {bar.instrument_id: bar for bar in bars}
    indicator_rows = (
        session.query(IndicatorValue)
        .filter(
            IndicatorValue.instrument_id.in_(instrument_ids),
            IndicatorValue.trade_date == trade_date,
            IndicatorValue.indicator_name == "sma",
            IndicatorValue.component == "value",
            IndicatorValue.parameter_signature == sma_parameter_signature,
        )
        .all()
    )
    sma_map = {row.instrument_id: row.value for row in indicator_rows}

    member_changes: list[GroupMemberChange] = []
    above_sma_count = 0
    for instrument_id in instrument_ids:
        instrument = instruments.get(instrument_id)
        bar = bar_map.get(instrument_id)
        if instrument is None or bar is None:
            continue
        close_change_pct = _resolve_close_change_pct(bar)
        member_changes.append(
            GroupMemberChange(
                instrument_id=instrument_id,
                symbol=instrument.symbol,
                close_change_pct=close_change_pct,
            )
        )
        sma_value = sma_map.get(instrument_id)
        if sma_value is not None and bar.close > sma_value:
            above_sma_count += 1

    if not member_changes:
        return GroupSummaryRead(
            member_count=0,
            average_close_change_pct=Decimal("0"),
            top_gainers=[],
            top_losers=[],
            percentage_above_sma=Decimal("0"),
        )

    average_close_change_pct = sum(
        (item.close_change_pct for item in member_changes),
        Decimal("0"),
    ) / Decimal(len(member_changes))
    sorted_members = sorted(member_changes, key=lambda item: item.close_change_pct, reverse=True)
    percentage_above_sma = (Decimal(above_sma_count) / Decimal(len(member_changes))) * Decimal("100")
    return GroupSummaryRead(
        member_count=len(member_changes),
        average_close_change_pct=average_close_change_pct.quantize(Decimal("0.000001")),
        top_gainers=sorted_members[:3],
        top_losers=list(reversed(sorted_members[-3:])),
        percentage_above_sma=percentage_above_sma.quantize(Decimal("0.000001")),
    )


def _resolve_close_change_pct(bar: DailyBar) -> Decimal:
    if bar.change_percent is not None:
        return bar.change_percent
    if bar.open == 0:
        return Decimal("0")
    return (((bar.close - bar.open) / bar.open) * Decimal("100")).quantize(Decimal("0.000001"))
