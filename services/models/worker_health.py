from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from services.db.base import Base


class WorkerHealth(Base):
    __tablename__ = "worker_health"
    __table_args__ = (Index("ix_worker_health_worker_name", "worker_name", unique=True),)

    id: Mapped[int] = mapped_column(primary_key=True)
    worker_name: Mapped[str] = mapped_column(String(128), nullable=False)
    worker_role: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    heartbeat_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_job_name: Mapped[str | None] = mapped_column(String(64))
    last_job_status: Mapped[str | None] = mapped_column(String(32))
    last_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
