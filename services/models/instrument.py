from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.db.base import Base

if TYPE_CHECKING:
    from services.models.daily_bar import DailyBar
    from services.models.indicator_value import IndicatorValue
    from services.models.instrument_tag import InstrumentTag
    from services.models.series_point import SeriesPoint
    from services.models.watchlist_item import WatchlistItem


class Instrument(Base):
    __tablename__ = "instruments"

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    market: Mapped[str] = mapped_column(String(32), index=True)
    asset_type: Mapped[str] = mapped_column(String(32), index=True)
    currency: Mapped[str] = mapped_column(String(8))
    timezone: Mapped[str] = mapped_column(String(64))
    source_route: Mapped[str] = mapped_column(String(64))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    daily_bars: Mapped[list["DailyBar"]] = relationship(back_populates="instrument")
    indicator_values: Mapped[list["IndicatorValue"]] = relationship(back_populates="instrument")
    tags: Mapped[list["InstrumentTag"]] = relationship(back_populates="instrument")
    series_points: Mapped[list["SeriesPoint"]] = relationship(back_populates="instrument")
    watchlist_items: Mapped[list["WatchlistItem"]] = relationship(back_populates="instrument")
