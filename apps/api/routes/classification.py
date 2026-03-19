from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from services.core.classification import (
    add_instrument_to_watchlist,
    add_tag_to_instrument,
    create_watchlist,
    get_watchlist,
    list_tags_for_instrument,
    list_watchlist_items,
    remove_instrument_from_watchlist,
    remove_tag_from_instrument,
    summarize_tag_group,
    summarize_watchlist_group,
)
from services.db.session import get_db_session
from services.schemas.classification import (
    GroupSummaryRead,
    InstrumentTagCreate,
    InstrumentTagRead,
    WatchlistCreate,
    WatchlistItemRead,
    WatchlistRead,
)

router = APIRouter(tags=["classification"])


@router.post("/instruments/{instrument_id}/tags", response_model=InstrumentTagRead)
async def create_instrument_tag(
    instrument_id: int,
    payload: InstrumentTagCreate,
    session: Session = Depends(get_db_session),
) -> InstrumentTagRead:
    tag = add_tag_to_instrument(session, instrument_id=instrument_id, tag=payload.tag)
    return InstrumentTagRead.model_validate(tag)


@router.get("/instruments/{instrument_id}/tags", response_model=list[InstrumentTagRead])
async def get_instrument_tags(
    instrument_id: int,
    session: Session = Depends(get_db_session),
) -> list[InstrumentTagRead]:
    tags = list_tags_for_instrument(session, instrument_id=instrument_id)
    return [InstrumentTagRead.model_validate(tag) for tag in tags]


@router.delete("/instruments/{instrument_id}/tags/{tag}")
async def delete_instrument_tag(
    instrument_id: int,
    tag: str,
    session: Session = Depends(get_db_session),
) -> dict[str, bool]:
    removed = remove_tag_from_instrument(session, instrument_id=instrument_id, tag=tag)
    if not removed:
        raise HTTPException(status_code=404, detail="tag not found")
    return {"removed": True}


@router.post("/watchlists", response_model=WatchlistRead)
async def create_watchlist_route(
    payload: WatchlistCreate,
    session: Session = Depends(get_db_session),
) -> WatchlistRead:
    watchlist = create_watchlist(session, name=payload.name, description=payload.description)
    return WatchlistRead.model_validate(watchlist)


@router.post("/watchlists/{watchlist_id}/items/{instrument_id}", response_model=WatchlistItemRead)
async def add_watchlist_item_route(
    watchlist_id: int,
    instrument_id: int,
    session: Session = Depends(get_db_session),
) -> WatchlistItemRead:
    if get_watchlist(session, watchlist_id=watchlist_id) is None:
        raise HTTPException(status_code=404, detail="watchlist not found")
    item = add_instrument_to_watchlist(session, watchlist_id=watchlist_id, instrument_id=instrument_id)
    return WatchlistItemRead.model_validate(item)


@router.delete("/watchlists/{watchlist_id}/items/{instrument_id}")
async def delete_watchlist_item_route(
    watchlist_id: int,
    instrument_id: int,
    session: Session = Depends(get_db_session),
) -> dict[str, bool]:
    removed = remove_instrument_from_watchlist(
        session,
        watchlist_id=watchlist_id,
        instrument_id=instrument_id,
    )
    if not removed:
        raise HTTPException(status_code=404, detail="watchlist item not found")
    return {"removed": True}


@router.get("/watchlists/{watchlist_id}/items", response_model=list[WatchlistItemRead])
async def get_watchlist_items_route(
    watchlist_id: int,
    session: Session = Depends(get_db_session),
) -> list[WatchlistItemRead]:
    if get_watchlist(session, watchlist_id=watchlist_id) is None:
        raise HTTPException(status_code=404, detail="watchlist not found")
    items = list_watchlist_items(session, watchlist_id=watchlist_id)
    return [WatchlistItemRead.model_validate(item) for item in items]


@router.get("/tags/{tag}/summary", response_model=GroupSummaryRead)
async def get_tag_summary_route(
    tag: str,
    trade_date: date,
    session: Session = Depends(get_db_session),
) -> GroupSummaryRead:
    return summarize_tag_group(session, tag=tag, trade_date=trade_date)


@router.get("/watchlists/{watchlist_id}/summary", response_model=GroupSummaryRead)
async def get_watchlist_summary_route(
    watchlist_id: int,
    trade_date: date,
    session: Session = Depends(get_db_session),
) -> GroupSummaryRead:
    if get_watchlist(session, watchlist_id=watchlist_id) is None:
        raise HTTPException(status_code=404, detail="watchlist not found")
    return summarize_watchlist_group(session, watchlist_id=watchlist_id, trade_date=trade_date)
