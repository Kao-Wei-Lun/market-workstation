from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WorkerHealthRead(BaseModel):
    id: int
    worker_name: str
    worker_role: str
    status: str
    heartbeat_at: datetime
    last_job_name: str | None = None
    last_job_status: str | None = None
    last_error: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
