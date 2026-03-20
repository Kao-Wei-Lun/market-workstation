from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from apps.api.main import app
from services.core.bootstrap import DEFAULT_V1_UNIVERSE_PRESET, load_instrument_universe
from services.db.base import Base
from services.db.session import get_db_session
from services.models import import_models
from services.models.daily_bar import DailyBar
from services.models.indicator_value import IndicatorValue
from services.models.ingest_job import IngestJob
from services.models.instrument import Instrument
from services.models.report_daily import ReportDaily
from services.models.worker_health import WorkerHealth


def _build_session() -> Session:
    import_models()
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return session_factory()


def _seed_system_data(session: Session) -> None:
    load_instrument_universe(session, preset_name=DEFAULT_V1_UNIVERSE_PRESET)
    trade_date = date(2026, 3, 20)
    tw_instrument = session.query(Instrument).filter(Instrument.symbol == "2330").one()
    us_instrument = session.query(Instrument).filter(Instrument.symbol == "AAPL").one()
    session.add(
        DailyBar(
            instrument_id=tw_instrument.id,
            trade_date=trade_date,
            open=Decimal("100"),
            high=Decimal("102"),
            low=Decimal("99"),
            close=Decimal("101"),
            volume=1000,
            change_percent=Decimal("1"),
        )
    )
    session.add(
        IndicatorValue(
            instrument_id=tw_instrument.id,
            trade_date=trade_date,
            indicator_name="ema",
            component="value",
            parameter_signature="period=20",
            value=Decimal("100"),
        )
    )
    session.add(
        DailyBar(
            instrument_id=us_instrument.id,
            trade_date=trade_date - timedelta(days=10),
            open=Decimal("200"),
            high=Decimal("202"),
            low=Decimal("198"),
            close=Decimal("201"),
            volume=2000,
            change_percent=Decimal("0.5"),
        )
    )
    session.add(
        ReportDaily(
            report_date=trade_date,
            report_type="market_summary",
            report_key="market",
            title="市場摘要",
            content_json={"trade_date": trade_date.isoformat()},
            markdown_text="# 市場摘要",
        )
    )
    session.add(
        IngestJob(
            source_route="twse_openapi",
            job_type="daily_market_etl",
            status="success",
            trade_date=trade_date,
            started_at=datetime.now(tz=UTC) - timedelta(minutes=15),
            finished_at=datetime.now(tz=UTC) - timedelta(minutes=10),
        )
    )
    session.add(
        WorkerHealth(
            worker_name="scheduler-worker",
            worker_role="scheduler",
            status="running",
            heartbeat_at=datetime.now(tz=UTC),
            last_job_name="daily_market_etl",
            last_job_status="success",
            last_error=None,
        )
    )
    session.commit()


@pytest.mark.asyncio
async def test_system_routes_return_coverage_and_status_payloads() -> None:
    session = _build_session()
    _seed_system_data(session)

    async def override_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db_session] = override_db
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        coverage_response = await client.get("/api/system/coverage")
        status_response = await client.get("/api/system/status", params={"job_limit": 10})

    app.dependency_overrides.clear()

    assert coverage_response.status_code == 200
    assert coverage_response.json()["data"]["preset"]["preset_name"] == DEFAULT_V1_UNIVERSE_PRESET
    assert coverage_response.json()["data"]["scopes"]
    assert coverage_response.json()["data"]["completeness"]["reference_latest_date"] == "2026-03-20"
    assert any(scope["status"] in {"partial", "stale", "ready", "missing"} for scope in coverage_response.json()["data"]["scopes"])
    assert any(scope["stale_data_count"] >= 1 for scope in coverage_response.json()["data"]["scopes"])
    assert status_response.status_code == 200
    assert status_response.json()["data"]["datasets"]
    assert status_response.json()["data"]["recent_jobs"][0]["job_type"] == "daily_market_etl"
    assert status_response.json()["data"]["workers"][0]["worker_name"] == "scheduler-worker"


@pytest.mark.asyncio
async def test_system_routes_handle_empty_status_payload() -> None:
    session = _build_session()

    async def override_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db_session] = override_db
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        status_response = await client.get("/api/system/status")

    app.dependency_overrides.clear()

    assert status_response.status_code == 200
    assert status_response.json()["meta"]["is_empty"] is False
    assert status_response.json()["data"]["recent_jobs"] == []


@pytest.mark.asyncio
async def test_manual_task_center_route_returns_actions() -> None:
    session = _build_session()
    _seed_system_data(session)

    async def override_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db_session] = override_db
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/system/tasks", params={"limit": 5})

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["available_actions"]
    assert payload["data"]["available_actions"][0]["action_key"] == "demo_data"


@pytest.mark.asyncio
async def test_manual_task_route_executes_and_records_history(monkeypatch) -> None:
    session = _build_session()
    _seed_system_data(session)

    async def override_db():
        try:
            yield session
        finally:
            pass

    def fake_execute_manual_task(session: Session, *, action_key: str, trade_date):
        assert action_key == "candidate_generation"
        assert trade_date == date(2026, 3, 20)
        job = IngestJob(
            source_route="manual_task_api",
            job_type="manual_task:candidate_generation",
            status="success",
            trade_date=trade_date,
            started_at=datetime.now(tz=UTC) - timedelta(minutes=1),
            finished_at=datetime.now(tz=UTC),
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        return {
            "action_key": "candidate_generation",
            "label": "產生候選清單",
            "target_label": "候選清單",
            "target_route_name": "candidates",
            "status": "success",
            "trade_date": trade_date,
            "metrics": {"candidate_items_created": 4},
            "message": "產生候選清單已完成。",
            "history_item": {
                "id": job.id,
                "action_key": "candidate_generation",
                "label": "產生候選清單",
                "description": "依現有指標、群組與衍生性商品脈絡產生隔日候選。",
                "target_label": "候選清單",
                "status": "success",
                "trade_date": trade_date,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "finished_at": job.finished_at.isoformat() if job.finished_at else None,
                "error_summary": None,
                "source_route": "manual_task_api",
                "job_type": "manual_task:candidate_generation",
            },
        }

    monkeypatch.setattr("apps.api.routes.tasks.execute_manual_task", fake_execute_manual_task)
    app.dependency_overrides[get_db_session] = override_db
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/system/tasks/candidate_generation",
            json={"trade_date": "2026-03-20"},
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["metrics"]["candidate_items_created"] == 4
    assert payload["history_item"]["job_type"] == "manual_task:candidate_generation"
