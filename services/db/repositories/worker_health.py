from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import desc
from sqlalchemy.orm import Session

from services.models.worker_health import WorkerHealth


class WorkerHealthRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_heartbeat(
        self,
        *,
        worker_name: str,
        worker_role: str,
        status: str,
        last_job_name: str | None = None,
        last_job_status: str | None = None,
        last_error: str | None = None,
    ) -> WorkerHealth:
        record = (
            self.session.query(WorkerHealth)
            .filter(WorkerHealth.worker_name == worker_name)
            .one_or_none()
        )
        heartbeat_at = datetime.now(tz=timezone.utc)
        if record is None:
            record = WorkerHealth(
                worker_name=worker_name,
                worker_role=worker_role,
                status=status,
                heartbeat_at=heartbeat_at,
                last_job_name=last_job_name,
                last_job_status=last_job_status,
                last_error=last_error,
            )
            self.session.add(record)
        else:
            record.worker_role = worker_role
            record.status = status
            record.heartbeat_at = heartbeat_at
            record.last_job_name = last_job_name
            record.last_job_status = last_job_status
            record.last_error = last_error

        self.session.flush()
        return record

    def get_by_worker_name(self, worker_name: str) -> WorkerHealth | None:
        return (
            self.session.query(WorkerHealth)
            .filter(WorkerHealth.worker_name == worker_name)
            .one_or_none()
        )

    def list_all(self) -> list[WorkerHealth]:
        return (
            self.session.query(WorkerHealth)
            .order_by(WorkerHealth.worker_role.asc(), WorkerHealth.worker_name.asc(), desc(WorkerHealth.heartbeat_at))
            .all()
        )
