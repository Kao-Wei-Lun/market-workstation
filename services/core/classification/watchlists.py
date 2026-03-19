from __future__ import annotations

from sqlalchemy.orm import Session

from services.models.watchlist import Watchlist
from services.models.watchlist_item import WatchlistItem


def create_watchlist(session: Session, *, name: str, description: str | None = None) -> Watchlist:
    watchlist = Watchlist(name=name, description=description)
    session.add(watchlist)
    session.flush()
    return watchlist


def add_instrument_to_watchlist(
    session: Session,
    *,
    watchlist_id: int,
    instrument_id: int,
) -> WatchlistItem:
    existing = (
        session.query(WatchlistItem)
        .filter(
            WatchlistItem.watchlist_id == watchlist_id,
            WatchlistItem.instrument_id == instrument_id,
        )
        .one_or_none()
    )
    if existing is not None:
        return existing
    item = WatchlistItem(watchlist_id=watchlist_id, instrument_id=instrument_id)
    session.add(item)
    session.flush()
    return item


def remove_instrument_from_watchlist(
    session: Session,
    *,
    watchlist_id: int,
    instrument_id: int,
) -> bool:
    existing = (
        session.query(WatchlistItem)
        .filter(
            WatchlistItem.watchlist_id == watchlist_id,
            WatchlistItem.instrument_id == instrument_id,
        )
        .one_or_none()
    )
    if existing is None:
        return False
    session.delete(existing)
    session.flush()
    return True


def list_watchlist_items(session: Session, *, watchlist_id: int) -> list[WatchlistItem]:
    return (
        session.query(WatchlistItem)
        .filter(WatchlistItem.watchlist_id == watchlist_id)
        .order_by(WatchlistItem.instrument_id.asc())
        .all()
    )


def get_watchlist(session: Session, *, watchlist_id: int) -> Watchlist | None:
    return session.query(Watchlist).filter(Watchlist.id == watchlist_id).one_or_none()
