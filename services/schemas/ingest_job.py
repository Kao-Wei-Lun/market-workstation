from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class IngestJobBase(BaseModel):
    source_route: str
    job_type: str
    status: str
    trade_date: date | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    retry_count: int = 0
    failure_reason: str | None = None


class IngestJobCreate(IngestJobBase):
    pass


class IngestJobRead(IngestJobBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
