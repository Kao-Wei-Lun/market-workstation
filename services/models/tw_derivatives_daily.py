from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.db.base import Base

if TYPE_CHECKING:
    from services.models.tw_derivatives_feature import TwDerivativesFeature


class TwDerivativesDaily(Base):
    __tablename__ = "tw_derivatives_daily"
    __table_args__ = (
        Index(
            "ix_tw_derivatives_daily_trade_date_market_product_institution",
            "trade_date",
            "market",
            "product_code",
            "institution",
            "contract_period",
            "call_put",
            unique=True,
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    market: Mapped[str] = mapped_column(String(32), nullable=False)
    product_code: Mapped[str] = mapped_column(String(32), nullable=False)
    product_name: Mapped[str | None] = mapped_column(String(128))
    contract_period: Mapped[str | None] = mapped_column(String(32))
    institution: Mapped[str] = mapped_column(String(64), nullable=False)
    call_put: Mapped[str | None] = mapped_column(String(16))
    long_open_interest: Mapped[int] = mapped_column(nullable=False)
    short_open_interest: Mapped[int] = mapped_column(nullable=False)
    net_open_interest: Mapped[int] = mapped_column(nullable=False)
    long_amount: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))
    short_amount: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))
    net_amount: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))
    source_route: Mapped[str] = mapped_column(String(64), nullable=False)
    is_options: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    features: Mapped["TwDerivativesFeature | None"] = relationship(
        back_populates="daily_record",
        uselist=False,
    )
