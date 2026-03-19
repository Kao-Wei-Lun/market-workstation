from __future__ import annotations

from sqlalchemy.orm import Session

from services.db.repositories.worker_health import WorkerHealthRepository
from services.models.worker_health import WorkerHealth


def record_worker_heartbeat(
    session: Session,
    *,
    worker_name: str,
    worker_role: str,
    status: str,
    last_job_name: str | None = None,
    last_job_status: str | None = None,
    last_error: str | None = None,
) -> WorkerHealth:
    return WorkerHealthRepository(session).upsert_heartbeat(
        worker_name=worker_name,
        worker_role=worker_role,
        status=status,
        last_job_name=last_job_name,
        last_job_status=last_job_status,
        last_error=last_error,
    )
