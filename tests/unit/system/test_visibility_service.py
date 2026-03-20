from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from services.core.bootstrap import DEFAULT_V1_UNIVERSE_PRESET, load_instrument_universe
from services.core.visibility import build_system_status, build_universe_coverage
from services.db.base import Base
from services.models import import_models
from services.models.candidate_run import CandidateRun
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


def test_build_universe_coverage_returns_config_and_loaded_counts() -> None:
    session = _build_session()
    load_instrument_universe(session, preset_name=DEFAULT_V1_UNIVERSE_PRESET)

    coverage = build_universe_coverage(session)

    assert coverage.meta.is_empty is False
    assert coverage.data.preset.preset_name == DEFAULT_V1_UNIVERSE_PRESET
    assert coverage.data.preset.configured_instrument_count >= 1
    assert coverage.data.scopes
    assert any(scope.loaded_instrument_count >= 1 for scope in coverage.data.scopes)
    assert coverage.data.market_counts
    assert coverage.summary_cards[0].label == "已載入標的"


def test_build_system_status_reports_dataset_freshness_jobs_and_workers() -> None:
    session = _build_session()
    load_instrument_universe(session, preset_name=DEFAULT_V1_UNIVERSE_PRESET)
    instrument = session.query(Instrument).order_by(Instrument.id.asc()).first()
    assert instrument is not None

    trade_date = date(2026, 3, 20)
    session.add(
        DailyBar(
            instrument_id=instrument.id,
            trade_date=trade_date,
            open=Decimal("100"),
            high=Decimal("101"),
            low=Decimal("99"),
            close=Decimal("100"),
            volume=1000,
            change_percent=Decimal("1"),
        )
    )
    session.add(
        IndicatorValue(
            instrument_id=instrument.id,
            trade_date=trade_date,
            indicator_name="sma",
            component="value",
            parameter_signature="period=20",
            value=Decimal("99"),
        )
    )
    session.add(
        CandidateRun(
            candidate_date=trade_date,
            status="success",
            total_candidates=1,
            generation_config_json={},
            summary_json={},
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
            status="failed",
            trade_date=trade_date,
            started_at=datetime.now(tz=UTC) - timedelta(minutes=10),
            finished_at=datetime.now(tz=UTC) - timedelta(minutes=5),
            failure_reason="demo failure",
        )
    )
    session.add(
        WorkerHealth(
            worker_name="analysis-worker",
            worker_role="analysis",
            status="idle",
            heartbeat_at=datetime.now(tz=UTC) - timedelta(minutes=45),
            last_job_name="daily_report_generation",
            last_job_status="success",
            last_error=None,
        )
    )
    session.commit()

    status = build_system_status(session, job_limit=10, worker_stale_minutes=30)

    assert status.meta.is_empty is False
    assert any(dataset.dataset_key == "daily_bars" and dataset.status == "ready" for dataset in status.data.datasets)
    assert status.data.recent_jobs[0].status == "failed"
    assert status.data.workers[0].stale is True
    assert any(card.key == "failed_jobs" for card in status.summary_cards)
