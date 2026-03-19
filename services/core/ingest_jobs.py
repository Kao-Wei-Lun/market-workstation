from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from services.db.repositories.ingest_jobs import IngestJobRepository
from services.models.ingest_job import IngestJob


def record_job_start(
    session: Session,
    *,
    source_route: str,
    job_type: str,
    trade_date: date | None = None,
    retry_count: int = 0,
) -> IngestJob:
    repository = IngestJobRepository(session)
    return repository.create(
        source_route=source_route,
        job_type=job_type,
        status="running",
        trade_date=trade_date,
        retry_count=retry_count,
    )


def record_job_success(session: Session, job: IngestJob) -> IngestJob:
    return IngestJobRepository(session).mark_success(job)


def record_job_failure(session: Session, job: IngestJob, failure_reason: str) -> IngestJob:
    return IngestJobRepository(session).mark_failure(job, failure_reason)
