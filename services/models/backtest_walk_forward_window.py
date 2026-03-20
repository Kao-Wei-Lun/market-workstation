from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import Date, DateTime, ForeignKey, JSON, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.db.base import Base

if TYPE_CHECKING:
    from services.models.backtest_run import BacktestRun
    from services.models.backtest_walk_forward_run import BacktestWalkForwardRun


class BacktestWalkForwardWindow(Base):
    __tablename__ = "backtest_walk_forward_windows"

    id: Mapped[int] = mapped_column(primary_key=True)
    walk_forward_run_id: Mapped[int] = mapped_column(ForeignKey("backtest_walk_forward_runs.id"), nullable=False)
    backtest_run_id: Mapped[int] = mapped_column(ForeignKey("backtest_runs.id"), nullable=False)
    window_index: Mapped[int] = mapped_column(nullable=False)
    train_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    train_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    test_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    test_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    selected_parameters_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    train_metrics_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    test_metrics_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    ranking_score: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    run: Mapped["BacktestWalkForwardRun"] = relationship(back_populates="windows")
    backtest_run: Mapped["BacktestRun"] = relationship()
