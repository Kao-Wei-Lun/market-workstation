from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.db.base import Base

if TYPE_CHECKING:
    from services.models.instrument import Instrument


class IndicatorValue(Base):
    __tablename__ = "indicator_values"
    __table_args__ = (
        Index(
            "ix_indicator_values_lookup",
            "instrument_id",
            "trade_date",
            "indicator_name",
            "component",
            "parameter_signature",
            unique=True,
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    indicator_name: Mapped[str] = mapped_column(String(64), nullable=False)
    component: Mapped[str] = mapped_column(String(64), nullable=False)
    parameter_signature: Mapped[str] = mapped_column(String(128), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    instrument: Mapped["Instrument"] = relationship(back_populates="indicator_values")
