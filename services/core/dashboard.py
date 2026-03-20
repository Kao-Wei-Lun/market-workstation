from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Literal

from sqlalchemy.orm import Session

from services.core.backtesting.service import list_backtest_runs, list_backtest_trades
from services.core.candidates.service import (
    get_latest_candidate_run,
    get_latest_candidate_run_for_date,
    list_candidate_items,
)
from services.core.classification.scanner import scan_tag_group, scan_watchlist_group
from services.core.classification.summary import summarize_tag_group, summarize_watchlist_group
from services.core.classification.watchlists import get_watchlist, list_watchlists
from services.core.derivatives.summary import (
    DailyInstitutionalBiasSummary,
    get_latest_institutional_bias_summary,
    load_daily_institutional_bias_summary,
)
from services.core.reports.service import (
    build_latest_market_snapshot,
    get_latest_report_date,
    list_reports,
)
from services.models.instrument_tag import InstrumentTag
from services.schemas.backtesting import BacktestRunRead, BacktestTradeRead
from services.schemas.candidates import CandidateItemRead, CandidateRunRead
from services.schemas.classification import GroupMemberChange, WatchlistRead
from services.schemas.output import (
    BacktestSummarySnapshotRead,
    BacktestsDashboardRead,
    CandidateSummarySnapshotRead,
    CandidatesDashboardRead,
    DashboardMetaRead,
    DashboardOverviewDataRead,
    DashboardOverviewRead,
    DashboardRankedItemRead,
    DashboardRankedListRead,
    DashboardSummaryCardRead,
    DerivativesDashboardRead,
    GroupDashboardRead,
    GroupSummarySnapshotRead,
    ReportSummarySnapshotRead,
    ReportsDashboardRead,
    WatchlistDashboardRead,
    WatchlistSummarySnapshotRead,
)
from services.schemas.reporting import ReportDailyRead


def build_dashboard_overview(
    session: Session,
    *,
    trade_date: date | None = None,
    watchlist_id: int | None = None,
    tag: str | None = None,
    top_n: int = 5,
) -> DashboardOverviewRead:
    market_report = build_latest_market_snapshot(session, report_date=trade_date)
    if market_report is None:
        return DashboardOverviewRead(
            meta=_meta(as_of_date=None, is_empty=True),
            summary_cards=[],
            highlights=["No daily market snapshot is available yet."],
            ranked_lists=[],
            data=DashboardOverviewDataRead(),
        )

    as_of_date = market_report.content.trade_date
    watchlist_summary = (
        build_watchlist_dashboard(session, watchlist_id=watchlist_id, trade_date=as_of_date, top_n=top_n).data
        if watchlist_id is not None
        else None
    )
    group_summary = (
        build_group_dashboard(session, tag=tag, trade_date=as_of_date, top_n=top_n).data
        if tag is not None
        else None
    )
    candidate_summary = build_candidates_dashboard(session, candidate_date=as_of_date, limit=top_n).data
    derivatives_summary = _load_derivatives_summary(session, as_of_date=as_of_date)
    backtest_summary = build_backtests_dashboard(session, limit=top_n).data
    report_summary = build_reports_dashboard(session, report_date=as_of_date, limit=top_n).data

    summary_cards = [
        _card("advancers", "Advancers", market_report.content.advancers, tone="positive"),
        _card("decliners", "Decliners", market_report.content.decliners, tone="negative"),
        _card(
            "above_sma20",
            "Above SMA20",
            _decimal_text(market_report.content.percentage_above_sma20),
            tone=_tone_from_percentage(market_report.content.percentage_above_sma20),
        ),
    ]
    if candidate_summary is not None:
        summary_cards.append(
            _card("candidates", "Candidates", candidate_summary.run.total_candidates, tone="info")
        )
    if derivatives_summary is not None:
        summary_cards.append(
            _card(
                "derivatives_regime",
                "Derivatives Regime",
                derivatives_summary.overall_regime,
                tone=_tone_from_regime(derivatives_summary.overall_regime),
            )
        )

    highlights = [
        f"Average close change {market_report.content.average_close_change_pct}%",
        f"Top gainer {market_report.content.top_gainers[0].symbol}" if market_report.content.top_gainers else "No top gainers",
    ]
    if candidate_summary is not None and candidate_summary.top_items:
        highlights.append(f"Top candidate {candidate_summary.top_items[0].symbol}")
    if derivatives_summary is not None:
        highlights.append(f"Derivatives regime {derivatives_summary.overall_regime}")

    ranked_lists = [
        _member_ranked_list("top_gainers", "Top Gainers", market_report.content.top_gainers[:top_n]),
        _member_ranked_list("top_losers", "Top Losers", market_report.content.top_losers[:top_n]),
        _group_ranked_list(session, as_of_date=as_of_date, top_n=top_n),
        _watchlist_ranked_list(session, as_of_date=as_of_date, top_n=top_n),
    ]
    if candidate_summary is not None:
        ranked_lists.append(
            DashboardRankedListRead(
                key="top_candidates",
                title="Top Candidates",
                item_count=len(candidate_summary.top_items),
                items=[
                    DashboardRankedItemRead(
                        key=str(item.instrument_id),
                        label=item.symbol,
                        primary_value=_decimal_text(item.score),
                        secondary_value=f"rank {item.rank}",
                        hint=", ".join(item.candidate_reasons[:2]),
                    )
                    for item in candidate_summary.top_items[:top_n]
                ],
            )
        )

    item_count = sum(len(ranked_list.items) for ranked_list in ranked_lists)
    return DashboardOverviewRead(
        meta=_meta(as_of_date=as_of_date, is_empty=False, item_count=item_count),
        summary_cards=summary_cards,
        highlights=highlights,
        ranked_lists=ranked_lists,
        data=DashboardOverviewDataRead(
            market_snapshot=market_report.content,
            watchlist_summary=watchlist_summary,
            group_summary=group_summary,
            candidate_summary=candidate_summary,
            derivatives_summary=derivatives_summary,
            backtest_summary=backtest_summary,
            report_summary=report_summary,
        ),
    )


def build_watchlist_dashboard(
    session: Session,
    *,
    watchlist_id: int,
    trade_date: date | None = None,
    top_n: int = 5,
) -> WatchlistDashboardRead:
    watchlist = get_watchlist(session, watchlist_id=watchlist_id)
    if watchlist is None:
        return WatchlistDashboardRead(
            meta=_meta(as_of_date=trade_date, is_empty=True),
            summary_cards=[],
            highlights=["Watchlist not found."],
            ranked_lists=[],
            data=None,
        )
    as_of_date = trade_date or _resolve_as_of_date(session)
    if as_of_date is None:
        return WatchlistDashboardRead(
            meta=_meta(as_of_date=None, is_empty=True),
            summary_cards=[],
            highlights=["No market data is available yet."],
            ranked_lists=[],
            data=None,
        )
    summary = summarize_watchlist_group(session, watchlist_id=watchlist_id, trade_date=as_of_date)
    scanner = scan_watchlist_group(session, watchlist_id=watchlist_id, trade_date=as_of_date)
    snapshot = WatchlistSummarySnapshotRead(
        watchlist=WatchlistRead.model_validate(watchlist),
        trade_date=as_of_date,
        summary=summary,
        scanner=scanner,
    )
    ranked_lists = [
        _member_ranked_list("watchlist_gainers", "Top Gainers", summary.top_gainers[:top_n]),
        _member_ranked_list("watchlist_losers", "Top Losers", summary.top_losers[:top_n]),
        DashboardRankedListRead(
            key="watchlist_flags",
            title="Scanner Flags",
            item_count=len(scanner.flagged_instruments),
            items=[
                DashboardRankedItemRead(
                    key=str(item.instrument_id),
                    label=item.symbol,
                    primary_value=_decimal_text(item.close_change_pct),
                    secondary_value=_decimal_text(item.volume_ratio) if item.volume_ratio is not None else None,
                    hint=", ".join(item.reasons),
                )
                for item in scanner.flagged_instruments[:top_n]
            ],
        ),
    ]
    return WatchlistDashboardRead(
        meta=_meta(as_of_date=as_of_date, is_empty=False, item_count=scanner.member_count),
        summary_cards=[
            _card("members", "Members", summary.member_count),
            _card("avg_change", "Average Change", _decimal_text(summary.average_close_change_pct), tone=_tone_from_percentage(summary.average_close_change_pct)),
            _card("above_sma", "Above SMA", _decimal_text(summary.percentage_above_sma), tone=_tone_from_percentage(summary.percentage_above_sma)),
        ],
        highlights=[
            f"Watchlist {watchlist.name}",
            f"{len(scanner.flagged_instruments)} scanner flags",
        ],
        ranked_lists=ranked_lists,
        data=snapshot,
    )


def build_group_dashboard(
    session: Session,
    *,
    tag: str,
    trade_date: date | None = None,
    top_n: int = 5,
) -> GroupDashboardRead:
    as_of_date = trade_date or _resolve_as_of_date(session)
    if as_of_date is None:
        return GroupDashboardRead(
            meta=_meta(as_of_date=None, is_empty=True),
            summary_cards=[],
            highlights=["No market data is available yet."],
            ranked_lists=[],
            data=None,
        )
    normalized_tag = tag.strip().lower()
    summary = summarize_tag_group(session, tag=normalized_tag, trade_date=as_of_date)
    scanner = scan_tag_group(session, tag=normalized_tag, trade_date=as_of_date)
    snapshot = GroupSummarySnapshotRead(
        tag=normalized_tag,
        trade_date=as_of_date,
        summary=summary,
        scanner=scanner,
    )
    return GroupDashboardRead(
        meta=_meta(as_of_date=as_of_date, is_empty=summary.member_count == 0, item_count=summary.member_count),
        summary_cards=[
            _card("members", "Members", summary.member_count),
            _card("avg_change", "Average Change", _decimal_text(summary.average_close_change_pct), tone=_tone_from_percentage(summary.average_close_change_pct)),
            _card("above_sma", "Above SMA", _decimal_text(summary.percentage_above_sma), tone=_tone_from_percentage(summary.percentage_above_sma)),
        ],
        highlights=[f"Group {normalized_tag}", f"{len(scanner.flagged_instruments)} scanner flags"],
        ranked_lists=[
            _member_ranked_list("group_gainers", "Top Gainers", summary.top_gainers[:top_n]),
            _member_ranked_list("group_losers", "Top Losers", summary.top_losers[:top_n]),
        ],
        data=snapshot,
    )


def build_candidates_dashboard(
    session: Session,
    *,
    candidate_date: date | None = None,
    limit: int = 10,
    offset: int = 0,
) -> CandidatesDashboardRead:
    run = (
        get_latest_candidate_run_for_date(session, candidate_date)
        if candidate_date is not None
        else get_latest_candidate_run(session)
    )
    if run is None:
        return CandidatesDashboardRead(
            meta=_meta(as_of_date=candidate_date, is_empty=True, limit=limit, offset=offset),
            summary_cards=[],
            highlights=["No candidate runs are available yet."],
            ranked_lists=[],
            data=None,
        )
    all_items = list_candidate_items(session, run.id)
    items = all_items[offset : offset + limit]
    snapshot = CandidateSummarySnapshotRead(
        run=CandidateRunRead.model_validate(run),
        top_items=[CandidateItemRead.model_validate(item) for item in items],
    )
    return CandidatesDashboardRead(
        meta=_meta(
            as_of_date=run.candidate_date,
            is_empty=len(all_items) == 0,
            item_count=len(all_items),
            returned_count=len(items),
            limit=limit,
            offset=offset,
        ),
        summary_cards=[
            _card("candidate_count", "Candidate Count", run.total_candidates),
            _card("regime", "Derivatives Regime", run.summary_json.get("overall_derivatives_regime", "unknown")),
        ],
        highlights=[
            f"{run.total_candidates} candidates generated",
            f"Run date {run.candidate_date.isoformat()}",
        ],
        ranked_lists=[
            DashboardRankedListRead(
                key="candidates",
                title="Candidates",
                item_count=len(items),
                items=[
                    DashboardRankedItemRead(
                        key=str(item.instrument_id),
                        label=item.symbol,
                        primary_value=_decimal_text(item.score),
                        secondary_value=f"rank {item.rank}",
                        hint=", ".join(item.candidate_reasons[:2]),
                    )
                    for item in snapshot.top_items
                ],
            )
        ],
        data=snapshot,
    )


def build_derivatives_dashboard(
    session: Session,
    *,
    trade_date: date | None = None,
) -> DerivativesDashboardRead:
    summary = _load_derivatives_summary(session, as_of_date=trade_date)
    if summary is None:
        return DerivativesDashboardRead(
            meta=_meta(as_of_date=trade_date, is_empty=True),
            summary_cards=[],
            highlights=["No derivatives summary is available yet."],
            ranked_lists=[],
            data=None,
        )
    return DerivativesDashboardRead(
        meta=_meta(as_of_date=summary.trade_date, is_empty=False, item_count=len(summary.highlights)),
        summary_cards=[
            _card("regime", "Overall Regime", summary.overall_regime, tone=_tone_from_regime(summary.overall_regime)),
            _card("bias", "Average Bias", _decimal_text(summary.average_bias_score), tone=_tone_from_percentage(summary.average_bias_score)),
            _card("anomalies", "Anomalies", summary.anomaly_count, tone="info"),
        ],
        highlights=summary.highlights,
        ranked_lists=[
            DashboardRankedListRead(
                key="derivatives_highlights",
                title="Highlights",
                item_count=len(summary.highlights),
                items=[
                    DashboardRankedItemRead(
                        key=str(index),
                        label=highlight,
                        primary_value=summary.overall_regime,
                    )
                    for index, highlight in enumerate(summary.highlights, start=1)
                ],
            )
        ],
        data=summary,
    )


def build_backtests_dashboard(
    session: Session,
    *,
    limit: int = 5,
) -> BacktestsDashboardRead:
    runs = list_backtest_runs(session, limit=limit)
    if not runs:
        return BacktestsDashboardRead(
            meta=_meta(as_of_date=None, is_empty=True, limit=limit),
            summary_cards=[],
            highlights=["No backtest runs are available yet."],
            ranked_lists=[],
            data=None,
        )
    latest_run = runs[0]
    trades = list_backtest_trades(session, latest_run.id)[:limit]
    snapshot = BacktestSummarySnapshotRead(
        latest_run=BacktestRunRead.model_validate(latest_run),
        recent_runs=[BacktestRunRead.model_validate(run) for run in runs],
        recent_trades=[BacktestTradeRead.model_validate(trade) for trade in trades],
    )
    sharpe = latest_run.metrics_json.get("sharpe_ratio", "0")
    return BacktestsDashboardRead(
        meta=_meta(as_of_date=latest_run.created_at.date(), is_empty=False, item_count=len(runs), limit=limit),
        summary_cards=[
            _card("total_return_pct", "Latest Return %", str(latest_run.total_return_pct), tone=_tone_from_percentage(latest_run.total_return_pct)),
            _card("win_rate", "Win Rate", str(latest_run.win_rate), tone=_tone_from_percentage(latest_run.win_rate)),
            _card("sharpe", "Sharpe", str(sharpe), tone="info"),
        ],
        highlights=[f"Latest run {latest_run.id}", f"{latest_run.total_trades} trades"],
        ranked_lists=[
            DashboardRankedListRead(
                key="recent_backtests",
                title="Recent Backtests",
                item_count=len(runs),
                items=[
                    DashboardRankedItemRead(
                        key=str(run.id),
                        label=f"Run {run.id}",
                        primary_value=str(run.total_return_pct),
                        secondary_value=f"{run.total_trades} trades",
                        hint=f"strategy {run.strategy_id}",
                    )
                    for run in runs
                ],
            ),
            DashboardRankedListRead(
                key="recent_trades",
                title="Recent Trades",
                item_count=len(trades),
                items=[
                    DashboardRankedItemRead(
                        key=str(trade.id),
                        label=f"Instrument {trade.instrument_id}",
                        primary_value=str(trade.net_pnl),
                        secondary_value=trade.exit_reason,
                        hint=f"{trade.entry_date.isoformat()} -> {trade.exit_date.isoformat()}",
                    )
                    for trade in trades
                ],
            ),
        ],
        data=snapshot,
    )


def build_reports_dashboard(
    session: Session,
    *,
    report_date: date | None = None,
    limit: int = 10,
    offset: int = 0,
) -> ReportsDashboardRead:
    resolved_date = report_date or get_latest_report_date(session)
    if resolved_date is None:
        return ReportsDashboardRead(
            meta=_meta(as_of_date=None, is_empty=True, limit=limit, offset=offset),
            summary_cards=[],
            highlights=["No reports are available yet."],
            ranked_lists=[],
            data=None,
        )
    all_reports = list_reports(session, report_date=resolved_date, limit=None)
    reports = all_reports[offset : offset + limit]
    snapshot = ReportSummarySnapshotRead(
        reports=[ReportDailyRead.model_validate(report) for report in reports]
    )
    return ReportsDashboardRead(
        meta=_meta(
            as_of_date=resolved_date,
            is_empty=len(all_reports) == 0,
            item_count=len(all_reports),
            returned_count=len(reports),
            limit=limit,
            offset=offset,
        ),
        summary_cards=[
            _card("report_count", "Reports", len(all_reports)),
            _card("bundle_present", "Bundle Present", "yes" if any(report.report_type == "daily_report_bundle" for report in all_reports) else "no", tone="info"),
        ],
        highlights=[f"Latest report date {resolved_date.isoformat()}"],
        ranked_lists=[
            DashboardRankedListRead(
                key="reports",
                title="Reports",
                item_count=len(reports),
                items=[
                    DashboardRankedItemRead(
                        key=str(report.id),
                        label=report.title,
                        primary_value=report.report_type,
                        secondary_value=report.report_key or None,
                    )
                    for report in snapshot.reports
                ],
            )
        ],
        data=snapshot,
    )


def _load_derivatives_summary(session: Session, *, as_of_date: date | None) -> DailyInstitutionalBiasSummary | None:
    if as_of_date is not None:
        summary = load_daily_institutional_bias_summary(session, trade_date=as_of_date)
        if summary.bullish_count or summary.bearish_count or summary.neutral_count:
            return summary
    return get_latest_institutional_bias_summary(session)


def _resolve_as_of_date(session: Session) -> date | None:
    market_report = build_latest_market_snapshot(session)
    return market_report.content.trade_date if market_report is not None else None


def _card(
    key: str,
    label: str,
    value: object,
    *,
    tone: Literal["positive", "negative", "neutral", "info"] = "neutral",
) -> DashboardSummaryCardRead:
    return DashboardSummaryCardRead(
        key=key,
        label=label,
        value=str(value),
        display_value=str(value),
        tone=tone,
    )


def _meta(
    *,
    as_of_date: date | None,
    is_empty: bool,
    item_count: int = 0,
    returned_count: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> DashboardMetaRead:
    resolved_returned = item_count if returned_count is None else returned_count
    return DashboardMetaRead(
        generated_at=datetime.now(tz=timezone.utc),
        as_of_date=as_of_date,
        is_empty=is_empty,
        item_count=item_count,
        returned_count=resolved_returned,
        limit=limit,
        offset=offset,
    )


def _member_ranked_list(key: str, title: str, members: list[GroupMemberChange]) -> DashboardRankedListRead:
    return DashboardRankedListRead(
        key=key,
        title=title,
        item_count=len(members),
        items=[
            DashboardRankedItemRead(
                key=str(member.instrument_id),
                label=member.symbol,
                primary_value=_decimal_text(member.close_change_pct),
            )
            for member in members
        ],
    )


def _group_ranked_list(session: Session, *, as_of_date: date, top_n: int) -> DashboardRankedListRead:
    tags = [tag for (tag,) in session.query(InstrumentTag.tag).distinct().order_by(InstrumentTag.tag.asc()).all()]
    ranked = []
    for tag in tags:
        summary = summarize_tag_group(session, tag=tag, trade_date=as_of_date)
        ranked.append(
            DashboardRankedItemRead(
                key=tag,
                label=tag,
                primary_value=_decimal_text(summary.average_close_change_pct),
                secondary_value=_decimal_text(summary.percentage_above_sma),
                hint=f"{summary.member_count} members",
            )
        )
    return DashboardRankedListRead(
        key="groups",
        title="Strongest Groups",
        item_count=min(len(ranked), top_n),
        items=sorted(ranked, key=lambda item: Decimal(item.primary_value), reverse=True)[:top_n],
    )


def _watchlist_ranked_list(session: Session, *, as_of_date: date, top_n: int) -> DashboardRankedListRead:
    ranked = []
    for watchlist in list_watchlists(session):
        summary = summarize_watchlist_group(session, watchlist_id=watchlist.id, trade_date=as_of_date)
        ranked.append(
            DashboardRankedItemRead(
                key=str(watchlist.id),
                label=watchlist.name,
                primary_value=_decimal_text(summary.average_close_change_pct),
                secondary_value=_decimal_text(summary.percentage_above_sma),
                hint=f"{summary.member_count} members",
            )
        )
    return DashboardRankedListRead(
        key="watchlists",
        title="Strongest Watchlists",
        item_count=min(len(ranked), top_n),
        items=sorted(ranked, key=lambda item: Decimal(item.primary_value), reverse=True)[:top_n],
    )


def _decimal_text(value: Decimal | None) -> str:
    return "n/a" if value is None else str(value)


def _tone_from_regime(regime: str) -> Literal["positive", "negative", "neutral", "info"]:
    if regime == "bullish":
        return "positive"
    if regime == "bearish":
        return "negative"
    return "neutral"


def _tone_from_percentage(value: Decimal) -> Literal["positive", "negative", "neutral", "info"]:
    if value > 0:
        return "positive"
    if value < 0:
        return "negative"
    return "neutral"
