from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.db.base import Base

if TYPE_CHECKING:
    from services.models.backtest_run import BacktestRun


class BacktestTrade(Base):
    __tablename__ = "backtest_trades"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("backtest_runs.id"), nullable=False)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), nullable=False)
    entry_date: Mapped[date] = mapped_column(Date, nullable=False)
    exit_date: Mapped[date] = mapped_column(Date, nullable=False)
    entry_price: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    exit_price: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    gross_pnl: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    net_pnl: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    fee_paid: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    tax_paid: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    slippage_paid: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    holding_period_days: Mapped[int] = mapped_column(nullable=False)
    exit_reason: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    run: Mapped["BacktestRun"] = relationship(back_populates="trades")
