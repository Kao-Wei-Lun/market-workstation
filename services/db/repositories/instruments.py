from __future__ import annotations

from datetime import date
from typing import cast

from sqlalchemy import func
from sqlalchemy.orm import Session

from services.models.daily_bar import DailyBar
from services.models.instrument import Instrument


class InstrumentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_symbol(self, symbol: str) -> Instrument | None:
        return (
            self.session.query(Instrument)
            .filter(Instrument.symbol == symbol, Instrument.is_active.is_(True))
            .one_or_none()
        )

    def list_for_chart_selection(
        self,
        *,
        query: str | None = None,
        market: str | None = None,
        asset_type: str | None = None,
        limit: int = 50,
    ) -> list[tuple[Instrument, date | None]]:
        statement = (
            self.session.query(Instrument, func.max(DailyBar.trade_date))
            .outerjoin(DailyBar, DailyBar.instrument_id == Instrument.id)
            .filter(Instrument.is_active.is_(True))
        )
        if query:
            normalized = f"%{query.strip().lower()}%"
            statement = statement.filter(
                func.lower(Instrument.symbol).like(normalized)
                | func.lower(Instrument.name).like(normalized)
            )
        if market:
            statement = statement.filter(Instrument.market == market)
        if asset_type:
            statement = statement.filter(Instrument.asset_type == asset_type)
        rows = (
            statement.group_by(Instrument.id)
            .order_by(Instrument.market.asc(), Instrument.asset_type.asc(), Instrument.symbol.asc())
            .limit(limit)
            .all()
        )
        return cast(list[tuple[Instrument, date | None]], rows)
