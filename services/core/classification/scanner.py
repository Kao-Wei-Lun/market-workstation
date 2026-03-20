from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from services.models.daily_bar import DailyBar
from services.models.indicator_value import IndicatorValue
from services.models.instrument import Instrument
from services.models.instrument_tag import InstrumentTag
from services.models.watchlist_item import WatchlistItem
from services.schemas.classification import (
    GroupMemberChange,
    GroupScannerFlagConditions,
    GroupScannerFlaggedInstrument,
    GroupScannerRead,
)


def scan_tag_group(
    session: Session,
    *,
    tag: str,
    trade_date: date,
    sma_parameter_signature: str = "period=20",
    volume_lookback_days: int = 20,
    flag_conditions: GroupScannerFlagConditions | None = None,
) -> GroupScannerRead:
    instrument_ids = [
        row.instrument_id
        for row in session.query(InstrumentTag.instrument_id)
        .filter(InstrumentTag.tag == tag.strip().lower())
        .all()
    ]
    return _build_group_scan(
        session,
        instrument_ids=instrument_ids,
        trade_date=trade_date,
        sma_parameter_signature=sma_parameter_signature,
        volume_lookback_days=volume_lookback_days,
        flag_conditions=flag_conditions or GroupScannerFlagConditions(),
    )


def scan_watchlist_group(
    session: Session,
    *,
    watchlist_id: int,
    trade_date: date,
    sma_parameter_signature: str = "period=20",
    volume_lookback_days: int = 20,
    flag_conditions: GroupScannerFlagConditions | None = None,
) -> GroupScannerRead:
    instrument_ids = [
        row.instrument_id
        for row in session.query(WatchlistItem.instrument_id)
        .filter(WatchlistItem.watchlist_id == watchlist_id)
        .all()
    ]
    return _build_group_scan(
        session,
        instrument_ids=instrument_ids,
        trade_date=trade_date,
        sma_parameter_signature=sma_parameter_signature,
        volume_lookback_days=volume_lookback_days,
        flag_conditions=flag_conditions or GroupScannerFlagConditions(),
    )


def _build_group_scan(
    session: Session,
    *,
    instrument_ids: list[int],
    trade_date: date,
    sma_parameter_signature: str,
    volume_lookback_days: int,
    flag_conditions: GroupScannerFlagConditions,
) -> GroupScannerRead:
    if not instrument_ids:
        return GroupScannerRead(
            member_count=0,
            average_daily_return_pct=Decimal("0"),
            top_gainers=[],
            top_losers=[],
            average_volume_ratio=None,
            percentage_above_sma=None,
            flagged_instruments=[],
        )

    instruments = {
        instrument.id: instrument
        for instrument in session.query(Instrument).filter(Instrument.id.in_(instrument_ids)).all()
    }
    bars = (
        session.query(DailyBar)
        .filter(DailyBar.instrument_id.in_(instrument_ids), DailyBar.trade_date <= trade_date)
        .order_by(DailyBar.instrument_id.asc(), DailyBar.trade_date.asc())
        .all()
    )
    bars_by_instrument: dict[int, list[DailyBar]] = defaultdict(list)
    for bar in bars:
        bars_by_instrument[bar.instrument_id].append(bar)

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
    flagged_instruments: list[GroupScannerFlaggedInstrument] = []
    volume_ratios: list[Decimal] = []
    above_sma_count = 0
    above_sma_denominator = 0

    for instrument_id in instrument_ids:
        instrument = instruments.get(instrument_id)
        if instrument is None:
            continue

        series = bars_by_instrument.get(instrument_id, [])
        current_bar = next((bar for bar in reversed(series) if bar.trade_date == trade_date), None)
        if current_bar is None:
            continue

        close_change_pct = _resolve_close_change_pct(current_bar)
        member_changes.append(
            GroupMemberChange(
                instrument_id=instrument_id,
                symbol=instrument.symbol,
                close_change_pct=close_change_pct,
            )
        )

        previous_bars = [bar for bar in series if bar.trade_date < trade_date][-volume_lookback_days:]
        volume_ratio = _compute_volume_ratio(current_bar, previous_bars)
        if volume_ratio is not None:
            volume_ratios.append(volume_ratio)

        sma_value = sma_map.get(instrument_id)
        above_sma: bool | None = None
        if sma_value is not None:
            above_sma = current_bar.close > sma_value
            above_sma_denominator += 1
            if above_sma:
                above_sma_count += 1

        reasons = _build_flag_reasons(
            close_change_pct=close_change_pct,
            volume_ratio=volume_ratio,
            above_sma=above_sma,
            conditions=flag_conditions,
        )
        if reasons:
            flagged_instruments.append(
                GroupScannerFlaggedInstrument(
                    instrument_id=instrument_id,
                    symbol=instrument.symbol,
                    close_change_pct=close_change_pct,
                    volume_ratio=volume_ratio,
                    above_sma=above_sma,
                    reasons=reasons,
                )
            )

    if not member_changes:
        return GroupScannerRead(
            member_count=0,
            average_daily_return_pct=Decimal("0"),
            top_gainers=[],
            top_losers=[],
            average_volume_ratio=None,
            percentage_above_sma=None,
            flagged_instruments=[],
        )

    sorted_members = sorted(member_changes, key=lambda item: item.close_change_pct, reverse=True)
    average_daily_return_pct = sum(
        (item.close_change_pct for item in member_changes),
        Decimal("0"),
    ) / Decimal(len(member_changes))
    average_volume_ratio = None
    if volume_ratios:
        average_volume_ratio = (
            sum(volume_ratios, Decimal("0")) / Decimal(len(volume_ratios))
        ).quantize(Decimal("0.000001"))

    percentage_above_sma = None
    if above_sma_denominator > 0:
        percentage_above_sma = (
            (Decimal(above_sma_count) / Decimal(above_sma_denominator)) * Decimal("100")
        ).quantize(Decimal("0.000001"))

    return GroupScannerRead(
        member_count=len(member_changes),
        average_daily_return_pct=average_daily_return_pct.quantize(Decimal("0.000001")),
        top_gainers=sorted_members[:3],
        top_losers=list(reversed(sorted_members[-3:])),
        average_volume_ratio=average_volume_ratio,
        percentage_above_sma=percentage_above_sma,
        flagged_instruments=flagged_instruments,
    )


def _build_flag_reasons(
    *,
    close_change_pct: Decimal,
    volume_ratio: Decimal | None,
    above_sma: bool | None,
    conditions: GroupScannerFlagConditions,
) -> list[str]:
    checks: list[tuple[bool, str]] = []
    if conditions.min_close_change_pct is not None:
        checks.append(
            (
                close_change_pct >= conditions.min_close_change_pct,
                f"close_change_pct>={conditions.min_close_change_pct}",
            )
        )
    if conditions.min_volume_ratio is not None:
        checks.append(
            (
                volume_ratio is not None and volume_ratio >= conditions.min_volume_ratio,
                f"volume_ratio>={conditions.min_volume_ratio}",
            )
        )
    if conditions.require_above_sma:
        checks.append((above_sma is True, "above_sma"))

    if not checks:
        return []

    matched_checks = [reason for matched, reason in checks if matched]
    if conditions.match_mode == "all":
        return matched_checks if len(matched_checks) == len(checks) else []
    return matched_checks


def _compute_volume_ratio(current_bar: DailyBar, previous_bars: list[DailyBar]) -> Decimal | None:
    if not previous_bars:
        return None
    average_volume = sum((Decimal(bar.volume) for bar in previous_bars), Decimal("0")) / Decimal(
        len(previous_bars)
    )
    if average_volume == 0:
        return None
    return (Decimal(current_bar.volume) / average_volume).quantize(Decimal("0.000001"))


def _resolve_close_change_pct(bar: DailyBar) -> Decimal:
    if bar.change_percent is not None:
        return bar.change_percent
    if bar.open == 0:
        return Decimal("0")
    return (((bar.close - bar.open) / bar.open) * Decimal("100")).quantize(Decimal("0.000001"))
