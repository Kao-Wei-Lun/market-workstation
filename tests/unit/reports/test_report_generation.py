from datetime import date
from decimal import Decimal
from typing import cast

from sqlalchemy.orm import Session

from services.core.reports.generators import (
    generate_group_summary_snapshot_report,
    generate_market_summary_report,
    generate_next_day_watch_candidates_report,
    generate_taiwan_derivatives_summary_report,
    generate_watchlist_summary_report,
)


def test_report_generators_build_structured_content_and_markdown(
    reporting_session: Session,
    reporting_seed: dict[str, object],
) -> None:
    report_date = cast(date, reporting_seed["report_date"])
    watchlist_id = cast(int, reporting_seed["watchlist_id"])
    tag = cast(str, reporting_seed["tag"])

    market_report = generate_market_summary_report(reporting_session, report_date=report_date)
    watchlist_report = generate_watchlist_summary_report(
        reporting_session,
        report_date=report_date,
        watchlist_id=watchlist_id,
    )
    group_report = generate_group_summary_snapshot_report(
        reporting_session,
        report_date=report_date,
        tag=tag,
    )
    derivatives_report = generate_taiwan_derivatives_summary_report(
        reporting_session,
        report_date=report_date,
    )
    candidates_report = generate_next_day_watch_candidates_report(
        reporting_session,
        report_date=report_date,
    )

    assert market_report.content.instrument_count == 3
    assert market_report.content.advancers == 2
    assert market_report.content.decliners == 1
    assert market_report.content.percentage_above_sma20 == Decimal("66.666667")
    assert "# Market Summary 2024-01-05" in market_report.markdown_text

    assert watchlist_report.content.watchlist_name == "focus"
    assert watchlist_report.content.summary.member_count == 2

    assert group_report.content.tag == "semiconductor"
    assert group_report.content.summary.member_count == 2

    assert derivatives_report.content.summary.overall_regime == "neutral"
    assert derivatives_report.content.summary.anomaly_count == 1

    assert candidates_report.content.candidate_count == 2
    assert candidates_report.content.candidates[0].symbol == "2330"
    assert "close_above_sma20" in candidates_report.content.candidates[0].reasons
