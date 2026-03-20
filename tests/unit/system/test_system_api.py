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
    instrument = session.query(Instrument).order_by(Instrument.id.asc()).first()
    assert instrument is not None
    trade_date = date(2026, 3, 20)
    session.add(
        DailyBar(
            instrument_id=instrument.id,
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
            instrument_id=instrument.id,
            trade_date=trade_date,
            indicator_name="ema",
            component="value",
            parameter_signature="period=20",
            value=Decimal("100"),
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
