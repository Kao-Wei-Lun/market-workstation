from __future__ import annotations

from datetime import date
from decimal import Decimal

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from apps.api.main import app
from services.db.base import Base
from services.db.session import get_db_session
from services.models import import_models
from services.models.daily_bar import DailyBar
from services.models.indicator_value import IndicatorValue
from services.models.instrument import Instrument


def _build_session() -> Session:
    import_models()
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return session_factory()


@pytest.mark.asyncio
async def test_classification_routes_cover_tag_watchlist_and_summary() -> None:
    session = _build_session()
    instrument = Instrument(
        symbol="2330",
        name="TSMC",
        market="TW",
        asset_type="stock",
        currency="TWD",
        timezone="Asia/Taipei",
        source_route="twse_openapi",
    )
    session.add(instrument)
    session.flush()
    session.add(
        DailyBar(
            instrument_id=instrument.id,
            trade_date=date(2024, 1, 5),
            open=Decimal("100"),
            high=Decimal("102"),
            low=Decimal("99"),
            close=Decimal("102"),
            volume=1000,
            change_percent=Decimal("2"),
        )
    )
    session.add(
        IndicatorValue(
            instrument_id=instrument.id,
            trade_date=date(2024, 1, 5),
            indicator_name="sma",
            component="value",
            parameter_signature="period=20",
            value=Decimal("100"),
        )
    )
    session.flush()

    async def override_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db_session] = override_db
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        tag_response = await client.post(f"/instruments/{instrument.id}/tags", json={"tag": "semiconductor"})
        list_tags_response = await client.get(f"/instruments/{instrument.id}/tags")
        watchlist_response = await client.post("/watchlists", json={"name": "chips"})
        watchlist_id = watchlist_response.json()["id"]
        add_item_response = await client.post(f"/watchlists/{watchlist_id}/items/{instrument.id}")
        summary_response = await client.get(f"/watchlists/{watchlist_id}/summary", params={"trade_date": "2024-01-05"})

    app.dependency_overrides.clear()

    assert tag_response.status_code == 200
    assert list_tags_response.status_code == 200
    assert watchlist_response.status_code == 200
    assert add_item_response.status_code == 200
    assert summary_response.status_code == 200
    assert summary_response.json()["member_count"] == 1
