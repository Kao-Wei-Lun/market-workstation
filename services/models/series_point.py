from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.db.base import Base

if TYPE_CHECKING:
    from services.models.instrument import Instrument


class SeriesPoint(Base):
    __tablename__ = "series_points"
    __table_args__ = (
        Index("ix_series_points_series_key_trade_date", "series_key", "trade_date", unique=True),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    instrument_id: Mapped[int | None] = mapped_column(ForeignKey("instruments.id"))
    series_key: Mapped[str] = mapped_column(String(128), nullable=False)
    source_route: Mapped[str] = mapped_column(String(64), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    instrument: Mapped["Instrument | None"] = relationship(back_populates="series_points")
