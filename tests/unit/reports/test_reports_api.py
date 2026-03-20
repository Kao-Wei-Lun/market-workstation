from __future__ import annotations

from datetime import date
from typing import cast

import httpx
import pytest
from sqlalchemy.orm import Session

from apps.api.main import app
from services.core.reports.bundle import generate_daily_report_bundle
from services.core.reports.generators import (
    MARKET_SUMMARY_REPORT,
    WATCHLIST_SUMMARY_REPORT,
    generate_market_summary_report,
    generate_watchlist_summary_report,
)
from services.core.reports.service import persist_generated_report
from services.db.session import get_db_session


@pytest.mark.asyncio
async def test_report_query_routes(
    reporting_session: Session,
    reporting_seed: dict[str, object],
) -> None:
    report_date = cast(date, reporting_seed["report_date"])
    watchlist_id = cast(int, reporting_seed["watchlist_id"])
    watchlist_key = cast(str, reporting_seed["watchlist_key"])

    persist_generated_report(
        reporting_session,
        generate_market_summary_report(reporting_session, report_date=report_date),
    )
    persist_generated_report(
        reporting_session,
        generate_watchlist_summary_report(
            reporting_session,
            report_date=report_date,
            watchlist_id=watchlist_id,
        ),
    )
    persist_generated_report(
        reporting_session,
        generate_daily_report_bundle(reporting_session, report_date=report_date),
    )

    async def override_db():
        try:
            yield reporting_session
        finally:
            pass

    app.dependency_overrides[get_db_session] = override_db
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        market_response = await client.get(f"/reports/{report_date.isoformat()}/{MARKET_SUMMARY_REPORT}")
        watchlist_response = await client.get(
            f"/reports/{report_date.isoformat()}/{WATCHLIST_SUMMARY_REPORT}",
            params={"report_key": watchlist_key},
        )
        bundle_response = await client.get(f"/reports/{report_date.isoformat()}/bundle")
        bundle_export_response = await client.get(
            f"/reports/{report_date.isoformat()}/bundle/export",
            params={"export_format": "csv"},
        )
        section_response = await client.get(
            f"/reports/{report_date.isoformat()}/bundle/sections/technical_breadth_summary"
        )
        list_response = await client.get("/reports", params={"report_date": report_date.isoformat()})
        latest_response = await client.get("/reports/latest")
        dashboard_response = await client.get(
            "/dashboard/overview/latest",
            params={"trade_date": report_date.isoformat(), "watchlist_id": watchlist_id},
        )
        derivatives_response = await client.get(f"/derivatives/summary/{report_date.isoformat()}")
        missing_response = await client.get(
            f"/reports/{report_date.isoformat()}/{WATCHLIST_SUMMARY_REPORT}"
        )

    app.dependency_overrides.clear()

    assert market_response.status_code == 200
    assert market_response.json()["content_json"]["instrument_count"] == 3
    assert watchlist_response.status_code == 200
    assert watchlist_response.json()["report_key"] == watchlist_key
    assert bundle_response.status_code == 200
    assert bundle_export_response.status_code == 200
    assert "section_type" in bundle_export_response.text
    assert bundle_response.json()["metadata"]["strongest_group_name"] == "semiconductor"
    assert section_response.status_code == 200
    assert section_response.json()["section_type"] == "technical_breadth_summary"
    assert list_response.status_code == 200
    assert len(list_response.json()) == 3
    assert latest_response.status_code == 200
    assert len(latest_response.json()) == 3
    assert dashboard_response.status_code == 200
    assert dashboard_response.json()["market_snapshot"]["instrument_count"] == 3
    assert derivatives_response.status_code == 200
    assert derivatives_response.json()["trade_date"] == report_date.isoformat()
    assert missing_response.status_code == 404
