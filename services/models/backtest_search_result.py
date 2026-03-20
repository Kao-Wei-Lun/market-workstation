from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, JSON, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.db.base import Base

if TYPE_CHECKING:
    from services.models.backtest_run import BacktestRun
    from services.models.backtest_search_run import BacktestSearchRun


class BacktestSearchResult(Base):
    __tablename__ = "backtest_search_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    search_run_id: Mapped[int] = mapped_column(ForeignKey("backtest_search_runs.id"), nullable=False)
    backtest_run_id: Mapped[int] = mapped_column(ForeignKey("backtest_runs.id"), nullable=False)
    parameter_set_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    metrics_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    ranking_score: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    rank: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    run: Mapped["BacktestSearchRun"] = relationship(back_populates="results")
    backtest_run: Mapped["BacktestRun"] = relationship()
