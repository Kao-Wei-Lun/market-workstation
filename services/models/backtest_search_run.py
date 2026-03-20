from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.db.base import Base

if TYPE_CHECKING:
    from services.models.backtest_search_result import BacktestSearchResult
    from services.models.strategy import Strategy


class BacktestSearchRun(Base):
    __tablename__ = "backtest_search_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    strategy_id: Mapped[int] = mapped_column(ForeignKey("strategies.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    ranking_metric: Mapped[str] = mapped_column(String(32), nullable=False)
    parameter_space_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    best_parameters_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    summary_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    strategy: Mapped["Strategy"] = relationship()
    results: Mapped[list["BacktestSearchResult"]] = relationship(back_populates="run")
