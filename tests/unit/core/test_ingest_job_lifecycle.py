from __future__ import annotations

from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from services.core.ingest_jobs import record_job_failure, record_job_start, record_job_success
from services.db.base import Base
from services.models import import_models
from services.models.ingest_job import IngestJob


def _build_session() -> Session:
    import_models()
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return session_factory()


def test_ingest_job_lifecycle_records_start_and_success() -> None:
    session = _build_session()

    job = record_job_start(
        session,
        source_route="twse_openapi",
        job_type="daily_bar_sync",
        trade_date=date(2024, 1, 2),
    )
    record_job_success(session, job)

    stored_job = session.query(IngestJob).one()
    assert stored_job.status == "success"
    assert stored_job.started_at is not None
    assert stored_job.finished_at is not None


def test_ingest_job_lifecycle_records_failure_reason() -> None:
    session = _build_session()

    job = record_job_start(session, source_route="macro_series_provider", job_type="series_sync")
    record_job_failure(session, job, "provider timeout")

    stored_job = session.query(IngestJob).one()
    assert stored_job.status == "failed"
    assert stored_job.failure_reason == "provider timeout"
