from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from services.core.classification.scanner import scan_tag_group, scan_watchlist_group
from services.core.reports.base import GeneratedReport
from services.core.reports.generators import (
    generate_market_summary_report,
    generate_next_day_watch_candidates_report,
    generate_taiwan_derivatives_summary_report,
)
from services.models.indicator_value import IndicatorValue
from services.models.instrument_tag import InstrumentTag
from services.models.watchlist import Watchlist
from services.schemas.reporting import (
    DailyReportBundleContent,
    DailyReportBundleMetadata,
    GroupScannerSummaryContent,
    RankedSummaryEntry,
    ReportSectionRead,
    TechnicalBreadthSummaryContent,
    TopMoversSummaryContent,
    WatchlistHighlightSummaryContent,
)

DAILY_REPORT_BUNDLE_REPORT = "daily_report_bundle"


def generate_daily_report_bundle(
    session: Session,
    *,
    report_date: date,
) -> GeneratedReport[DailyReportBundleContent]:
    market_report = generate_market_summary_report(session, report_date=report_date)
    derivatives_report = generate_taiwan_derivatives_summary_report(session, report_date=report_date)
    candidates_report = generate_next_day_watch_candidates_report(session, report_date=report_date)
    group_summary = _build_group_scanner_summary(session, report_date=report_date)
    watchlist_summary = _build_watchlist_highlight_summary(session, report_date=report_date)
    top_movers_summary = _build_top_movers_summary(market_report.content)
    breadth_summary = _build_technical_breadth_summary(
        session,
        report_date=report_date,
        market_report=market_report.content,
    )

    sections = [
        _build_section(
            title="Market Summary",
            section_type="market_summary",
            payload=market_report.content.model_dump(mode="json"),
            markdown_body=market_report.markdown_text,
        ),
        _build_section(
            title="Watchlist Summary",
            section_type="watchlist_summary",
            payload=watchlist_summary.model_dump(mode="json"),
            markdown_body=_watchlist_summary_markdown(watchlist_summary),
        ),
        _build_section(
            title="Group Scanner Summary",
            section_type="group_scanner_summary",
            payload=group_summary.model_dump(mode="json"),
            markdown_body=_group_scanner_markdown(group_summary),
        ),
        _build_section(
            title="Taiwan Derivatives Summary",
            section_type="taiwan_derivatives_summary",
            payload=derivatives_report.content.model_dump(mode="json"),
            markdown_body=derivatives_report.markdown_text,
        ),
        _build_section(
            title="Next-Day Candidate Summary",
            section_type="next_day_candidate_summary",
            payload=candidates_report.content.model_dump(mode="json"),
            markdown_body=candidates_report.markdown_text,
        ),
        _build_section(
            title="Top Movers Summary",
            section_type="top_movers_summary",
            payload=top_movers_summary.model_dump(mode="json"),
            markdown_body=_top_movers_markdown(top_movers_summary),
        ),
        _build_section(
            title="Technical Breadth Summary",
            section_type="technical_breadth_summary",
            payload=breadth_summary.model_dump(mode="json"),
            markdown_body=_technical_breadth_markdown(breadth_summary),
        ),
    ]

    metadata = DailyReportBundleMetadata(
        report_date=report_date,
        section_count=len(sections),
        strongest_group_name=_entry_name(group_summary.strongest_groups),
        weakest_group_name=_entry_name(group_summary.weakest_groups),
        strongest_watchlist_name=_entry_name(watchlist_summary.strongest_watchlists),
        weakest_watchlist_name=_entry_name(watchlist_summary.weakest_watchlists),
        top_candidate_symbols=[candidate.symbol for candidate in candidates_report.content.candidates[:5]],
    )
    content = DailyReportBundleContent(report_date=report_date, metadata=metadata, sections=sections)
    markdown_text = _bundle_markdown(content)
    return GeneratedReport(
        report_date=report_date,
        report_type=DAILY_REPORT_BUNDLE_REPORT,
        report_key="",
        title=f"Daily report bundle for {report_date.isoformat()}",
        content=content,
        markdown_text=markdown_text,
    )


def _build_group_scanner_summary(session: Session, *, report_date: date) -> GroupScannerSummaryContent:
    tags = [tag for (tag,) in session.query(InstrumentTag.tag).distinct().order_by(InstrumentTag.tag.asc()).all()]
    ranked_groups = []
    for tag in tags:
        scan = scan_tag_group(session, tag=tag, trade_date=report_date)
        ranked_groups.append(
            RankedSummaryEntry(
                name=tag,
                average_daily_return_pct=scan.average_daily_return_pct,
                percentage_above_sma=scan.percentage_above_sma,
                member_count=scan.member_count,
            )
        )
    strongest = sorted(
        ranked_groups,
        key=lambda item: (item.average_daily_return_pct, item.percentage_above_sma or Decimal("0")),
        reverse=True,
    )[:3]
    weakest = sorted(
        ranked_groups,
        key=lambda item: (item.average_daily_return_pct, item.percentage_above_sma or Decimal("0")),
    )[:3]
    return GroupScannerSummaryContent(
        trade_date=report_date,
        strongest_groups=strongest,
        weakest_groups=weakest,
    )


def _build_watchlist_highlight_summary(session: Session, *, report_date: date) -> WatchlistHighlightSummaryContent:
    ranked_watchlists = []
    for watchlist in session.query(Watchlist).order_by(Watchlist.id.asc()).all():
        scan = scan_watchlist_group(session, watchlist_id=watchlist.id, trade_date=report_date)
        ranked_watchlists.append(
            RankedSummaryEntry(
                name=watchlist.name,
                average_daily_return_pct=scan.average_daily_return_pct,
                percentage_above_sma=scan.percentage_above_sma,
                member_count=scan.member_count,
            )
        )
    strongest = sorted(
        ranked_watchlists,
        key=lambda item: (item.average_daily_return_pct, item.percentage_above_sma or Decimal("0")),
        reverse=True,
    )[:3]
    weakest = sorted(
        ranked_watchlists,
        key=lambda item: (item.average_daily_return_pct, item.percentage_above_sma or Decimal("0")),
    )[:3]
    return WatchlistHighlightSummaryContent(
        trade_date=report_date,
        strongest_watchlists=strongest,
        weakest_watchlists=weakest,
    )


def _build_top_movers_summary(market_summary) -> TopMoversSummaryContent:
    return TopMoversSummaryContent(
        trade_date=market_summary.trade_date,
        top_gainers=market_summary.top_gainers,
        top_losers=market_summary.top_losers,
    )


def _build_technical_breadth_summary(
    session: Session,
    *,
    report_date: date,
    market_report,
) -> TechnicalBreadthSummaryContent:
    momentum_rows = (
        session.query(IndicatorValue.instrument_id, IndicatorValue.value)
        .filter(
            IndicatorValue.trade_date == report_date,
            IndicatorValue.indicator_name == "rsi",
            IndicatorValue.component == "value",
            IndicatorValue.parameter_signature == "period=14",
        )
        .all()
    )
    positive_momentum_signal_count = sum(
        1 for _instrument_id, value in momentum_rows if Decimal("50") <= value <= Decimal("70")
    )
    return TechnicalBreadthSummaryContent(
        trade_date=report_date,
        instrument_count=market_report.instrument_count,
        gainers=market_report.advancers,
        losers=market_report.decliners,
        unchanged=market_report.unchanged,
        percentage_above_sma20=market_report.percentage_above_sma20,
        positive_momentum_signal_count=positive_momentum_signal_count,
    )


def _build_section(
    *,
    title: str,
    section_type: str,
    payload: dict[str, Any],
    markdown_body: str,
) -> ReportSectionRead:
    return ReportSectionRead(
        title=title,
        section_type=section_type,
        markdown_body=markdown_body,
        payload_json=payload,
    )


def _bundle_markdown(content: DailyReportBundleContent) -> str:
    lines = [
        f"# Daily Report Bundle {content.report_date.isoformat()}",
        "",
        f"- Sections: {content.metadata.section_count}",
        f"- Strongest group: {content.metadata.strongest_group_name or 'None'}",
        f"- Weakest group: {content.metadata.weakest_group_name or 'None'}",
        f"- Strongest watchlist: {content.metadata.strongest_watchlist_name or 'None'}",
        f"- Weakest watchlist: {content.metadata.weakest_watchlist_name or 'None'}",
        f"- Top candidates: {', '.join(content.metadata.top_candidate_symbols) or 'None'}",
    ]
    for section in content.sections:
        lines.extend(["", f"## {section.title}", "", section.markdown_body])
    return "\n".join(lines)


def _watchlist_summary_markdown(content: WatchlistHighlightSummaryContent) -> str:
    return "\n".join(
        [
            f"# Watchlist Highlights {content.trade_date.isoformat()}",
            "",
            "## Strongest watchlists",
            *_ranked_entry_lines(content.strongest_watchlists),
            "",
            "## Weakest watchlists",
            *_ranked_entry_lines(content.weakest_watchlists),
        ]
    )


def _group_scanner_markdown(content: GroupScannerSummaryContent) -> str:
    return "\n".join(
        [
            f"# Group Scanner Summary {content.trade_date.isoformat()}",
            "",
            "## Strongest groups",
            *_ranked_entry_lines(content.strongest_groups),
            "",
            "## Weakest groups",
            *_ranked_entry_lines(content.weakest_groups),
        ]
    )


def _top_movers_markdown(content: TopMoversSummaryContent) -> str:
    top_gainer_lines = [f"- {item.symbol}: {item.close_change_pct}%" for item in content.top_gainers] or ["- None"]
    top_loser_lines = [f"- {item.symbol}: {item.close_change_pct}%" for item in content.top_losers] or ["- None"]
    return "\n".join(
        [
            f"# Top Movers {content.trade_date.isoformat()}",
            "",
            "## Top gainers",
            *top_gainer_lines,
            "",
            "## Top losers",
            *top_loser_lines,
        ]
    )


def _technical_breadth_markdown(content: TechnicalBreadthSummaryContent) -> str:
    return "\n".join(
        [
            f"# Technical Breadth {content.trade_date.isoformat()}",
            "",
            f"- Instruments: {content.instrument_count}",
            f"- Gainers / Losers / Unchanged: {content.gainers} / {content.losers} / {content.unchanged}",
            f"- Above SMA20: {content.percentage_above_sma20}%",
            f"- Positive momentum signals: {content.positive_momentum_signal_count}",
        ]
    )


def _ranked_entry_lines(entries: list[RankedSummaryEntry]) -> list[str]:
    if not entries:
        return ["- None"]
    return [
        f"- {entry.name}: avg_return={entry.average_daily_return_pct}%, "
        f"above_sma={entry.percentage_above_sma}, members={entry.member_count}"
        for entry in entries
    ]


def _entry_name(entries: list[RankedSummaryEntry]) -> str | None:
    if not entries:
        return None
    return entries[0].name
