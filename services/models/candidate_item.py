from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.db.base import Base

if TYPE_CHECKING:
    from services.models.candidate_run import CandidateRun
    from services.models.instrument import Instrument


class CandidateItem(Base):
    __tablename__ = "candidate_items"
    __table_args__ = (
        Index("ix_candidate_items_run_id_rank", "run_id", "rank", unique=True),
        Index("ix_candidate_items_run_id_instrument_id", "run_id", "instrument_id", unique=True),
        Index("ix_candidate_items_candidate_date", "candidate_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("candidate_runs.id"), nullable=False)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), nullable=False)
    candidate_date: Mapped[date] = mapped_column(Date, nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    score: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    rank: Mapped[int] = mapped_column(nullable=False)
    candidate_reasons_json: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    supporting_metrics_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    run: Mapped["CandidateRun"] = relationship(back_populates="items")
    instrument: Mapped["Instrument"] = relationship()
