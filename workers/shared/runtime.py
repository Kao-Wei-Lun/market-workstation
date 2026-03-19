from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session, sessionmaker

from services.core.ingest_jobs import record_job_failure, record_job_start, record_job_success
from services.core.worker_health import record_worker_heartbeat
from services.models.ingest_job import IngestJob
from workers.shared.jobs import get_registered_job

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WorkerExecutionResult:
    job_name: str
    metrics: dict[str, int]


def run_registered_job(
    *,
    session_factory: sessionmaker[Session],
    worker_name: str,
    worker_role: str,
    job_name: str,
    trade_date: date,
) -> WorkerExecutionResult:
    job_definition = get_registered_job(job_name)
    _record_worker_status(
        session_factory,
        worker_name=worker_name,
        worker_role=worker_role,
        status="running",
        last_job_name=job_name,
        last_job_status="running",
        last_error=None,
    )
    ingest_job = _create_lifecycle_job(
        session_factory,
        source_route=f"worker:{worker_role}",
        job_type=job_name,
        trade_date=trade_date,
    )

    try:
        with session_factory() as session:
            result = job_definition.handler(session, trade_date)
        _mark_lifecycle_success(session_factory, ingest_job)
        _record_worker_status(
            session_factory,
            worker_name=worker_name,
            worker_role=worker_role,
            status="idle",
            last_job_name=job_name,
            last_job_status="success",
            last_error=None,
        )
        logger.info("worker job completed", extra={"job_name": job_name, "metrics": result.metrics})
        return WorkerExecutionResult(job_name=result.job_name, metrics=result.metrics)
    except Exception as exc:
        _mark_lifecycle_failure(session_factory, ingest_job, str(exc))
        _record_worker_status(
            session_factory,
            worker_name=worker_name,
            worker_role=worker_role,
            status="error",
            last_job_name=job_name,
            last_job_status="failed",
            last_error=str(exc),
        )
        logger.exception("worker job failed", extra={"job_name": job_name})
        raise


def record_worker_idle_heartbeat(
    *,
    session_factory: sessionmaker[Session],
    worker_name: str,
    worker_role: str,
) -> None:
    _record_worker_status(
        session_factory,
        worker_name=worker_name,
        worker_role=worker_role,
        status="idle",
        last_job_name=None,
        last_job_status=None,
        last_error=None,
    )


def _create_lifecycle_job(
    session_factory: sessionmaker[Session],
    *,
    source_route: str,
    job_type: str,
    trade_date: date,
) -> IngestJob:
    with session_factory() as session:
        job = record_job_start(
            session,
            source_route=source_route,
            job_type=job_type,
            trade_date=trade_date,
        )
        session.commit()
        session.refresh(job)
        return job


def _mark_lifecycle_success(session_factory: sessionmaker[Session], ingest_job: IngestJob) -> None:
    with session_factory() as session:
        job = session.get(IngestJob, ingest_job.id)
        if job is None:
            return
        record_job_success(session, job)
        session.commit()


def _mark_lifecycle_failure(
    session_factory: sessionmaker[Session],
    ingest_job: IngestJob,
    failure_reason: str,
) -> None:
    with session_factory() as session:
        job = session.get(IngestJob, ingest_job.id)
        if job is None:
            return
        record_job_failure(session, job, failure_reason)
        session.commit()


def _record_worker_status(
    session_factory: sessionmaker[Session],
    *,
    worker_name: str,
    worker_role: str,
    status: str,
    last_job_name: str | None,
    last_job_status: str | None,
    last_error: str | None,
) -> None:
    with session_factory() as session:
        record_worker_heartbeat(
            session,
            worker_name=worker_name,
            worker_role=worker_role,
            status=status,
            last_job_name=last_job_name,
            last_job_status=last_job_status,
            last_error=last_error,
        )
        session.commit()
