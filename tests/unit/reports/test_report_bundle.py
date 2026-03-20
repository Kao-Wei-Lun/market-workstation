from datetime import date
from typing import cast

from sqlalchemy.orm import Session

from services.core.reports.bundle import DAILY_REPORT_BUNDLE_REPORT, generate_daily_report_bundle
from services.core.reports.service import get_report_bundle, get_report_section, persist_generated_report


def test_daily_report_bundle_generation_builds_sections_and_highlights(
    reporting_session: Session,
    reporting_seed: dict[str, object],
) -> None:
    report_date = cast(date, reporting_seed["report_date"])

    bundle_report = generate_daily_report_bundle(reporting_session, report_date=report_date)

    assert bundle_report.report_type == DAILY_REPORT_BUNDLE_REPORT
    assert bundle_report.content.metadata.section_count == 7
    assert bundle_report.content.metadata.strongest_group_name == "semiconductor"
    assert bundle_report.content.metadata.weakest_group_name == "hardware"
    assert bundle_report.content.metadata.strongest_watchlist_name == "focus"
    assert bundle_report.content.metadata.weakest_watchlist_name == "laggards"
    assert bundle_report.content.metadata.top_candidate_symbols == ["2330", "2303"]
    assert [section.section_type for section in bundle_report.content.sections] == [
        "market_summary",
        "watchlist_summary",
        "group_scanner_summary",
        "taiwan_derivatives_summary",
        "next_day_candidate_summary",
        "top_movers_summary",
        "technical_breadth_summary",
    ]
    technical_breadth = next(
        section for section in bundle_report.content.sections if section.section_type == "technical_breadth_summary"
    )
    assert technical_breadth.payload_json["positive_momentum_signal_count"] == 2
    assert "Daily Report Bundle 2024-01-05" in bundle_report.markdown_text


def test_daily_report_bundle_persistence_and_section_helpers(
    reporting_session: Session,
    reporting_seed: dict[str, object],
) -> None:
    report_date = cast(date, reporting_seed["report_date"])
    bundle_report = generate_daily_report_bundle(reporting_session, report_date=report_date)

    persisted = persist_generated_report(reporting_session, bundle_report)
    fetched_bundle = get_report_bundle(reporting_session, report_date=report_date)
    fetched_section = get_report_section(
        reporting_session,
        report_date=report_date,
        section_type="next_day_candidate_summary",
    )

    assert persisted.id > 0
    assert fetched_bundle is not None
    assert fetched_bundle.metadata.top_candidate_symbols == ["2330", "2303"]
    assert fetched_section is not None
    assert fetched_section.title == "Next-Day Candidate Summary"
