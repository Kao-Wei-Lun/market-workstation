from __future__ import annotations

from sqlalchemy.orm import Session

from services.models.instrument import Instrument
from services.models.instrument_tag import InstrumentTag
from services.models.watchlist_item import WatchlistItem
from services.schemas.backtesting import StrategyDefinition


def resolve_universe_instrument_ids(session: Session, strategy: StrategyDefinition) -> list[int]:
    filters = strategy.universe
    query = session.query(Instrument.id).filter(Instrument.is_active.is_(True))
    if strategy.instrument_id is not None:
        query = query.filter(Instrument.id == strategy.instrument_id)
    if filters is not None:
        if filters.instrument_ids:
            query = query.filter(Instrument.id.in_(filters.instrument_ids))
        if filters.market is not None:
            query = query.filter(Instrument.market == filters.market)
        if filters.asset_type is not None:
            query = query.filter(Instrument.asset_type == filters.asset_type)
        if filters.required_tags:
            for tag in filters.required_tags:
                query = query.filter(
                    Instrument.id.in_(
                        session.query(InstrumentTag.instrument_id).filter(InstrumentTag.tag == tag)
                    )
                )
        if filters.watchlist_id is not None:
            query = query.filter(
                Instrument.id.in_(
                    session.query(WatchlistItem.instrument_id).filter(WatchlistItem.watchlist_id == filters.watchlist_id)
                )
            )
    return sorted({row.id for row in query.all()})
