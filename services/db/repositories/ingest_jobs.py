from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from services.models.ingest_job import IngestJob


class IngestJobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        source_route: str,
        job_type: str,
        status: str,
        trade_date=None,
        retry_count: int = 0,
    ) -> IngestJob:
        job = IngestJob(
            source_route=source_route,
            job_type=job_type,
            status=status,
            trade_date=trade_date,
            retry_count=retry_count,
            started_at=datetime.now(tz=timezone.utc),
        )
        self.session.add(job)
        self.session.flush()
        return job

    def mark_success(self, job: IngestJob) -> IngestJob:
        job.status = "success"
        job.finished_at = datetime.now(tz=timezone.utc)
        job.failure_reason = None
        self.session.flush()
        return job

    def mark_failure(self, job: IngestJob, failure_reason: str) -> IngestJob:
        job.status = "failed"
        job.finished_at = datetime.now(tz=timezone.utc)
        job.failure_reason = failure_reason
        self.session.flush()
        return job
