from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from services.core.classification.scanner import scan_tag_group, scan_watchlist_group
from services.schemas.classification import GroupScannerFlagConditions, GroupSummaryRead


def summarize_tag_group(
    session: Session,
    *,
    tag: str,
    trade_date: date,
    sma_parameter_signature: str = "period=20",
) -> GroupSummaryRead:
    scan_result = scan_tag_group(
        session,
        tag=tag,
        trade_date=trade_date,
        sma_parameter_signature=sma_parameter_signature,
        flag_conditions=GroupScannerFlagConditions(
            min_close_change_pct=None,
            min_volume_ratio=None,
            require_above_sma=False,
        ),
    )
    return GroupSummaryRead(
        member_count=scan_result.member_count,
        average_close_change_pct=scan_result.average_daily_return_pct,
        top_gainers=scan_result.top_gainers,
        top_losers=scan_result.top_losers,
        percentage_above_sma=scan_result.percentage_above_sma or Decimal("0"),
    )


def summarize_watchlist_group(
    session: Session,
    *,
    watchlist_id: int,
    trade_date: date,
    sma_parameter_signature: str = "period=20",
) -> GroupSummaryRead:
    scan_result = scan_watchlist_group(
        session,
        watchlist_id=watchlist_id,
        trade_date=trade_date,
        sma_parameter_signature=sma_parameter_signature,
        flag_conditions=GroupScannerFlagConditions(
            min_close_change_pct=None,
            min_volume_ratio=None,
            require_above_sma=False,
        ),
    )
    return GroupSummaryRead(
        member_count=scan_result.member_count,
        average_close_change_pct=scan_result.average_daily_return_pct,
        top_gainers=scan_result.top_gainers,
        top_losers=scan_result.top_losers,
        percentage_above_sma=scan_result.percentage_above_sma or Decimal("0"),
    )
