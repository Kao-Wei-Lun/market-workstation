from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.db.base import Base

if TYPE_CHECKING:
    from services.models.tw_derivatives_daily import TwDerivativesDaily


class TwDerivativesFeature(Base):
    __tablename__ = "tw_derivatives_features"

    id: Mapped[int] = mapped_column(primary_key=True)
    daily_record_id: Mapped[int] = mapped_column(
        ForeignKey("tw_derivatives_daily.id"),
        nullable=False,
        unique=True,
    )
    trade_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    market: Mapped[str] = mapped_column(String(32), nullable=False)
    product_code: Mapped[str] = mapped_column(String(32), nullable=False)
    contract_period: Mapped[str | None] = mapped_column(String(32))
    institution: Mapped[str] = mapped_column(String(64), nullable=False)
    call_put: Mapped[str | None] = mapped_column(String(16))
    delta_1d: Mapped[Decimal | None] = mapped_column(Numeric(20, 6))
    delta_5d: Mapped[Decimal | None] = mapped_column(Numeric(20, 6))
    delta_20d: Mapped[Decimal | None] = mapped_column(Numeric(20, 6))
    zscore_20d: Mapped[Decimal | None] = mapped_column(Numeric(20, 6))
    regime_label: Mapped[str] = mapped_column(String(32), nullable=False)
    bias_score: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    anomaly_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    daily_record: Mapped["TwDerivativesDaily"] = relationship(back_populates="features")
