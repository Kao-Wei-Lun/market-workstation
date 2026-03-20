from __future__ import annotations

from datetime import date
from typing import cast

import httpx
import pytest
from sqlalchemy.orm import Session

from apps.api.main import app
from services.db.session import get_db_session


@pytest.mark.asyncio
async def test_candidate_routes_generate_and_query_runs(
    reporting_session: Session,
    reporting_seed: dict[str, object],
) -> None:
    candidate_date = cast(date, reporting_seed["report_date"])

    async def override_db():
        try:
            yield reporting_session
        finally:
            pass

    app.dependency_overrides[get_db_session] = override_db
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        create_response = await client.post(
            "/candidates/runs",
            json={"candidate_date": candidate_date.isoformat(), "top_n": 10},
        )
        run_id = create_response.json()["run"]["id"]
        get_response = await client.get(f"/candidates/runs/{run_id}")
        list_runs_response = await client.get("/candidates/runs", params={"candidate_date": candidate_date.isoformat()})
        by_date_response = await client.get(f"/candidates/runs/by-date/{candidate_date.isoformat()}")
        items_response = await client.get(f"/candidates/runs/{run_id}/items")
        filtered_items_response = await client.get("/candidates/items", params={"candidate_date": candidate_date.isoformat(), "symbol": "2330"})
        latest_summary_response = await client.get("/candidates/summary/latest")
        export_response = await client.get(f"/candidates/runs/{run_id}/export", params={"export_format": "csv"})

    app.dependency_overrides.clear()

    assert create_response.status_code == 200
    assert create_response.json()["run"]["total_candidates"] == 2
    assert get_response.status_code == 200
    assert list_runs_response.status_code == 200
    assert by_date_response.status_code == 200
    assert items_response.status_code == 200
    assert filtered_items_response.status_code == 200
    assert latest_summary_response.status_code == 200
    assert export_response.status_code == 200
    assert "symbol" in export_response.text
    assert [item["symbol"] for item in items_response.json()] == ["2330", "2303"]
    assert [item["symbol"] for item in filtered_items_response.json()] == ["2330"]
