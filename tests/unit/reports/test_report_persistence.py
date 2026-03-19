from datetime import date
from typing import cast

from sqlalchemy.orm import Session

from services.core.reports.generators import (
    MARKET_SUMMARY_REPORT,
    WATCHLIST_SUMMARY_REPORT,
    generate_market_summary_report,
    generate_watchlist_summary_report,
)
from services.core.reports.service import get_report, list_reports, persist_generated_report


def test_report_persistence_and_query_helpers(
    reporting_session: Session,
    reporting_seed: dict[str, object],
) -> None:
    report_date = cast(date, reporting_seed["report_date"])
    watchlist_id = cast(int, reporting_seed["watchlist_id"])
    watchlist_key = cast(str, reporting_seed["watchlist_key"])

    market_report = generate_market_summary_report(reporting_session, report_date=report_date)
    watchlist_report = generate_watchlist_summary_report(
        reporting_session,
        report_date=report_date,
        watchlist_id=watchlist_id,
    )

    persisted_market = persist_generated_report(reporting_session, market_report)
    persisted_watchlist = persist_generated_report(reporting_session, watchlist_report)

    fetched_market = get_report(
        reporting_session,
        report_date=report_date,
        report_type=MARKET_SUMMARY_REPORT,
    )
    fetched_watchlist = get_report(
        reporting_session,
        report_date=report_date,
        report_type=WATCHLIST_SUMMARY_REPORT,
        report_key=watchlist_key,
    )
    listed = list_reports(reporting_session, report_date=report_date)

    assert persisted_market.id > 0
    assert persisted_watchlist.id > 0
    assert fetched_market is not None
    assert fetched_market.title == market_report.title
    assert fetched_market.content_json["instrument_count"] == 3
    assert fetched_watchlist is not None
    assert fetched_watchlist.content_json["watchlist_name"] == "focus"
    assert len(listed) == 2
