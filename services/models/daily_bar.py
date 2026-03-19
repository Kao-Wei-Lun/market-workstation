from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.db.base import Base

if TYPE_CHECKING:
    from services.models.instrument import Instrument


class DailyBar(Base):
    __tablename__ = "daily_bars"
    __table_args__ = (
        Index("ix_daily_bars_instrument_id_trade_date", "instrument_id", "trade_date", unique=True),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    open: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    volume: Mapped[int] = mapped_column(nullable=False)
    turnover_value: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))
    transactions_count: Mapped[int | None]
    change: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    change_percent: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    instrument: Mapped["Instrument"] = relationship(back_populates="daily_bars")
