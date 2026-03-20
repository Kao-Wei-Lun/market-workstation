from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Date, DateTime, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.db.base import Base

if TYPE_CHECKING:
    from services.models.candidate_item import CandidateItem


class CandidateRun(Base):
    __tablename__ = "candidate_runs"
    __table_args__ = (
        Index("ix_candidate_runs_candidate_date", "candidate_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    total_candidates: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    generation_config_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    summary_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    items: Mapped[list["CandidateItem"]] = relationship(back_populates="run")
