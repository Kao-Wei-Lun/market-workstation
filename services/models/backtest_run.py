from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, JSON, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.db.base import Base

if TYPE_CHECKING:
    from services.models.backtest_trade import BacktestTrade
    from services.models.strategy import Strategy


class BacktestRun(Base):
    __tablename__ = "backtest_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    strategy_id: Mapped[int] = mapped_column(ForeignKey("strategies.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    initial_cash: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    final_cash: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    total_return: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    total_return_pct: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    total_trades: Mapped[int] = mapped_column(nullable=False)
    win_rate: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    fee_paid: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    tax_paid: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    slippage_paid: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    resolved_parameters_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    metrics_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    notes: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    strategy: Mapped["Strategy"] = relationship(back_populates="backtest_runs")
    trades: Mapped[list["BacktestTrade"]] = relationship(back_populates="run")
