from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from services.db.base import Base


class TwInstitutionalSpotDaily(Base):
    __tablename__ = "tw_institutional_spot_daily"
    __table_args__ = (
        Index(
            "ix_tw_institutional_spot_daily_trade_date_market_institution",
            "trade_date",
            "market",
            "institution",
            unique=True,
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    market: Mapped[str] = mapped_column(String(32), nullable=False)
    institution: Mapped[str] = mapped_column(String(64), nullable=False)
    buy_amount: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    sell_amount: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    net_amount: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    source_route: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
