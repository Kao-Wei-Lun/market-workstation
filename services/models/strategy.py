from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.db.base import Base

if TYPE_CHECKING:
    from services.models.backtest_run import BacktestRun
    from services.models.instrument import Instrument


class Strategy(Base):
    __tablename__ = "strategies"

    id: Mapped[int] = mapped_column(primary_key=True)
    instrument_id: Mapped[int | None] = mapped_column(ForeignKey("instruments.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    definition_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    instrument: Mapped["Instrument"] = relationship()
    backtest_runs: Mapped[list["BacktestRun"]] = relationship(back_populates="strategy")
