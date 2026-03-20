from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from services.core.candidates.service import build_candidate_generation
from services.core.classification.summary import summarize_tag_group, summarize_watchlist_group
from services.core.derivatives.summary import generate_daily_institutional_bias_summary
from services.core.reports.base import GeneratedReport
from services.models.daily_bar import DailyBar
from services.models.indicator_value import IndicatorValue
from services.models.instrument import Instrument
from services.models.tw_derivatives_feature import TwDerivativesFeature
from services.models.watchlist import Watchlist
from services.schemas.classification import GroupMemberChange, GroupSummaryRead
from services.schemas.candidates import CandidateSummaryRead
from services.schemas.reporting import (
    GroupSummarySnapshotContent,
    MarketSummaryContent,
    NextDayWatchCandidate,
    NextDayWatchCandidatesContent,
    TaiwanDerivativesSummaryContent,
    WatchlistSummaryContent,
)

MARKET_SUMMARY_REPORT = "market_summary"
WATCHLIST_SUMMARY_REPORT = "watchlist_summary"
GROUP_SUMMARY_SNAPSHOT_REPORT = "group_summary_snapshot"
TAIWAN_DERIVATIVES_SUMMARY_REPORT = "taiwan_derivatives_summary"
NEXT_DAY_WATCH_CANDIDATES_REPORT = "next_day_watch_candidates"


def generate_market_summary_report(
    session: Session,
    *,
    report_date: date,
) -> GeneratedReport[MarketSummaryContent]:
    bars = (
        session.query(DailyBar, Instrument)
        .join(Instrument, Instrument.id == DailyBar.instrument_id)
        .filter(DailyBar.trade_date == report_date)
        .order_by(Instrument.symbol.asc())
        .all()
    )
    instrument_ids = [bar.instrument_id for bar, _instrument in bars]
    sma_map = _load_indicator_value_map(
        session,
        instrument_ids=instrument_ids,
        trade_date=report_date,
        indicator_name="sma",
        component="value",
        parameter_signature="period=20",
    )

    movers: list[GroupMemberChange] = []
    advancers = 0
    decliners = 0
    unchanged = 0
    above_sma_count = 0
    for bar, instrument in bars:
        change_percent = _resolve_close_change_pct(bar)
        movers.append(
            GroupMemberChange(
                instrument_id=instrument.id,
                symbol=instrument.symbol,
                close_change_pct=change_percent,
            )
        )
        if change_percent > 0:
            advancers += 1
        elif change_percent < 0:
            decliners += 1
        else:
            unchanged += 1

        sma20 = sma_map.get(bar.instrument_id)
        if sma20 is not None and bar.close > sma20:
            above_sma_count += 1

    content = MarketSummaryContent(
        trade_date=report_date,
        instrument_count=len(movers),
        advancers=advancers,
        decliners=decliners,
        unchanged=unchanged,
        average_close_change_pct=_average_change(movers),
        percentage_above_sma20=_percentage(above_sma_count, len(movers)),
        top_gainers=sorted(movers, key=lambda item: item.close_change_pct, reverse=True)[:5],
        top_losers=sorted(movers, key=lambda item: item.close_change_pct)[:5],
    )
    markdown_text = "\n".join(
        [
            f"# Market Summary {report_date.isoformat()}",
            "",
            f"- Instruments: {content.instrument_count}",
            f"- Advancers / Decliners / Unchanged: {content.advancers} / {content.decliners} / {content.unchanged}",
            f"- Average close change: {content.average_close_change_pct}%",
            f"- Above SMA20: {content.percentage_above_sma20}%",
            "",
            "## Top gainers",
            *_format_member_lines(content.top_gainers),
            "",
            "## Top losers",
            *_format_member_lines(content.top_losers),
        ]
    )
    return GeneratedReport(
        report_date=report_date,
        report_type=MARKET_SUMMARY_REPORT,
        report_key="",
        title=f"Market summary for {report_date.isoformat()}",
        content=content,
        markdown_text=markdown_text,
    )


def generate_watchlist_summary_report(
    session: Session,
    *,
    report_date: date,
    watchlist_id: int,
) -> GeneratedReport[WatchlistSummaryContent]:
    watchlist = session.query(Watchlist).filter(Watchlist.id == watchlist_id).one_or_none()
    if watchlist is None:
        msg = "watchlist not found"
        raise ValueError(msg)

    summary = summarize_watchlist_group(
        session,
        watchlist_id=watchlist_id,
        trade_date=report_date,
    )
    content = WatchlistSummaryContent(
        trade_date=report_date,
        watchlist_id=watchlist.id,
        watchlist_name=watchlist.name,
        summary=summary,
    )
    markdown_text = _group_summary_markdown(
        title=f"Watchlist summary: {watchlist.name}",
        report_date=report_date,
        summary=summary,
    )
    return GeneratedReport(
        report_date=report_date,
        report_type=WATCHLIST_SUMMARY_REPORT,
        report_key=f"watchlist:{watchlist.id}",
        title=f"Watchlist summary for {watchlist.name}",
        content=content,
        markdown_text=markdown_text,
    )


def generate_group_summary_snapshot_report(
    session: Session,
    *,
    report_date: date,
    tag: str,
) -> GeneratedReport[GroupSummarySnapshotContent]:
    normalized_tag = tag.strip().lower()
    summary = summarize_tag_group(session, tag=normalized_tag, trade_date=report_date)
    content = GroupSummarySnapshotContent(
        trade_date=report_date,
        tag=normalized_tag,
        summary=summary,
    )
    markdown_text = _group_summary_markdown(
        title=f"Group summary: {normalized_tag}",
        report_date=report_date,
        summary=summary,
    )
    return GeneratedReport(
        report_date=report_date,
        report_type=GROUP_SUMMARY_SNAPSHOT_REPORT,
        report_key=f"tag:{normalized_tag}",
        title=f"Group summary for tag {normalized_tag}",
        content=content,
        markdown_text=markdown_text,
    )


def generate_taiwan_derivatives_summary_report(
    session: Session,
    *,
    report_date: date,
) -> GeneratedReport[TaiwanDerivativesSummaryContent]:
    features = (
        session.query(TwDerivativesFeature)
        .filter(TwDerivativesFeature.trade_date == report_date)
        .order_by(
            TwDerivativesFeature.institution.asc(),
            TwDerivativesFeature.product_code.asc(),
            TwDerivativesFeature.call_put.asc(),
        )
        .all()
    )
    summary = generate_daily_institutional_bias_summary(report_date, features)
    content = TaiwanDerivativesSummaryContent(trade_date=report_date, summary=summary)
    markdown_text = "\n".join(
        [
            f"# Taiwan Derivatives Summary {report_date.isoformat()}",
            "",
            f"- Overall regime: {summary.overall_regime}",
            f"- Average bias score: {summary.average_bias_score}",
            f"- Bullish / Bearish / Neutral: {summary.bullish_count} / {summary.bearish_count} / {summary.neutral_count}",
            f"- Anomalies: {summary.anomaly_count}",
            "",
            "## Highlights",
            *[f"- {line}" for line in summary.highlights],
        ]
    )
    return GeneratedReport(
        report_date=report_date,
        report_type=TAIWAN_DERIVATIVES_SUMMARY_REPORT,
        report_key="",
        title=f"Taiwan derivatives summary for {report_date.isoformat()}",
        content=content,
        markdown_text=markdown_text,
    )


def generate_next_day_watch_candidates_report(
    session: Session,
    *,
    report_date: date,
) -> GeneratedReport[NextDayWatchCandidatesContent]:
    generation = build_candidate_generation(session, candidate_date=report_date, top_n=10)
    summary = generation.summary
    candidates = [
        NextDayWatchCandidate(
            instrument_id=item.instrument_id,
            symbol=item.symbol,
            candidate_date=item.candidate_date,
            score=item.score,
            rank=item.rank,
            reasons=item.candidate_reasons,
            supporting_metrics=item.supporting_metrics,
        )
        for item in generation.items
    ]
    content = NextDayWatchCandidatesContent(
        trade_date=report_date,
        candidate_count=len(candidates),
        summary=CandidateSummaryRead.model_validate(summary),
        candidates=candidates,
    )
    markdown_text = "\n".join(
        [
            f"# Next-Day Watch Candidates {report_date.isoformat()}",
            "",
            f"- Candidate count: {content.candidate_count}",
            f"- Derivatives regime: {content.summary.overall_derivatives_regime}",
            "",
            "## Candidates",
            *[
                f"- #{candidate.rank} {candidate.symbol}: score {candidate.score}, "
                f"reasons={', '.join(candidate.reasons)}"
                for candidate in content.candidates
            ],
        ]
    )
    return GeneratedReport(
        report_date=report_date,
        report_type=NEXT_DAY_WATCH_CANDIDATES_REPORT,
        report_key="",
        title=f"Next-day watch candidates for {report_date.isoformat()}",
        content=content,
        markdown_text=markdown_text,
    )


def _group_summary_markdown(
    *,
    title: str,
    report_date: date,
    summary: GroupSummaryRead,
) -> str:
    return "\n".join(
        [
            f"# {title}",
            "",
            f"- Trade date: {report_date.isoformat()}",
            f"- Members: {summary.member_count}",
            f"- Average close change: {summary.average_close_change_pct}%",
            f"- Above SMA20: {summary.percentage_above_sma}%",
            "",
            "## Top gainers",
            *_format_member_lines(summary.top_gainers),
            "",
            "## Top losers",
            *_format_member_lines(summary.top_losers),
        ]
    )


def _format_member_lines(members: list[GroupMemberChange]) -> list[str]:
    if not members:
        return ["- None"]
    return [f"- {member.symbol}: {member.close_change_pct}%" for member in members]


def _load_indicator_value_map(
    session: Session,
    *,
    instrument_ids: list[int],
    trade_date: date,
    indicator_name: str,
    component: str,
    parameter_signature: str,
) -> dict[int, Decimal]:
    if not instrument_ids:
        return {}

    rows = (
        session.query(IndicatorValue)
        .filter(
            IndicatorValue.instrument_id.in_(instrument_ids),
            IndicatorValue.trade_date == trade_date,
            IndicatorValue.indicator_name == indicator_name,
            IndicatorValue.component == component,
            IndicatorValue.parameter_signature == parameter_signature,
        )
        .all()
    )
    return {row.instrument_id: row.value for row in rows}


def _average_change(members: list[GroupMemberChange]) -> Decimal:
    if not members:
        return Decimal("0.000000")
    value = sum((member.close_change_pct for member in members), Decimal("0")) / Decimal(len(members))
    return value.quantize(Decimal("0.000001"))


def _percentage(numerator: int, denominator: int) -> Decimal:
    if denominator == 0:
        return Decimal("0.000000")
    return ((Decimal(numerator) / Decimal(denominator)) * Decimal("100")).quantize(Decimal("0.000001"))


def _resolve_close_change_pct(bar: DailyBar) -> Decimal:
    if bar.change_percent is not None:
        return bar.change_percent.quantize(Decimal("0.000001"))
    if bar.open == 0:
        return Decimal("0.000000")
    return (((bar.close - bar.open) / bar.open) * Decimal("100")).quantize(Decimal("0.000001"))
