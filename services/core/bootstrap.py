from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from services.connectors.base import ConnectorRequest
from services.connectors.dev_seed import StaticDailyBarConnector
from services.core.classification.tags import add_tag_to_instrument
from services.core.classification.watchlists import add_instrument_to_watchlist, create_watchlist
from services.core.etl.pipeline import run_ingestion_pipeline
from services.models.instrument import Instrument
from services.models.instrument_tag import InstrumentTag
from services.models.watchlist import Watchlist
from services.models.watchlist_item import WatchlistItem


@dataclass(frozen=True)
class SeedResult:
    instruments_created: int
    watchlists_created: int
    tags_created: int


@dataclass(frozen=True)
class SampleEtlResult:
    instruments_processed: int
    daily_bars_loaded: int


def seed_sample_reference_data(session: Session) -> SeedResult:
    sample_instruments = [
        {
            "symbol": "2330",
            "name": "TSMC",
            "market": "TW",
            "asset_type": "stock",
            "currency": "TWD",
            "timezone": "Asia/Taipei",
            "source_route": "twse_openapi",
        },
        {
            "symbol": "AAPL",
            "name": "Apple",
            "market": "US",
            "asset_type": "stock",
            "currency": "USD",
            "timezone": "America/New_York",
            "source_route": "us_eod_provider",
        },
        {
            "symbol": "^TWII",
            "name": "TAIEX",
            "market": "TW",
            "asset_type": "index",
            "currency": "TWD",
            "timezone": "Asia/Taipei",
            "source_route": "manual_csv",
        },
    ]

    instruments_created = 0
    tags_created = 0
    for payload in sample_instruments:
        instrument, created = _upsert_instrument(session, **payload)
        instruments_created += int(created)
        tags_created += _ensure_tag(session, instrument.id, "sample")
        if instrument.symbol == "2330":
            tags_created += _ensure_tag(session, instrument.id, "semiconductor")
        if instrument.symbol == "AAPL":
            tags_created += _ensure_tag(session, instrument.id, "us-tech")

    watchlist, created = _ensure_watchlist(session, name="sample-core", description="Sample development watchlist")
    watchlists_created = int(created)
    for symbol in ["2330", "AAPL"]:
        instrument = session.query(Instrument).filter(Instrument.symbol == symbol).one()
        _ensure_watchlist_item(session, watchlist.id, instrument.id)

    session.commit()
    return SeedResult(
        instruments_created=instruments_created,
        watchlists_created=watchlists_created,
        tags_created=tags_created,
    )


def run_sample_daily_market_etl(session: Session, *, trade_date: date) -> SampleEtlResult:
    seed_sample_reference_data(session)

    sample_series = {
        "2330": _build_price_series(
            trade_date=trade_date,
            start_price=Decimal("580"),
            daily_step=Decimal("2.5"),
            volume_base=1_500_000,
            market="TW",
        ),
        "AAPL": _build_price_series(
            trade_date=trade_date,
            start_price=Decimal("180"),
            daily_step=Decimal("1.2"),
            volume_base=900_000,
            market="US",
        ),
    }

    instruments_processed = 0
    daily_bars_loaded = 0
    for symbol, rows in sample_series.items():
        instrument = session.query(Instrument).filter(Instrument.symbol == symbol).one()
        connector = StaticDailyBarConnector(
            payload={"data": rows},
            market=instrument.market,
            currency=instrument.currency,
        )
        request = ConnectorRequest(
            symbol=instrument.symbol,
            trade_date=trade_date,
            instrument_id=instrument.id,
            source_route=instrument.source_route,
        )
        load_result = run_ingestion_pipeline(
            session,
            connector=connector,
            request=request,
            job_type="sample_daily_market_sync",
        )
        session.commit()
        instruments_processed += 1
        daily_bars_loaded += load_result.daily_bars_loaded

    return SampleEtlResult(
        instruments_processed=instruments_processed,
        daily_bars_loaded=daily_bars_loaded,
    )


def _upsert_instrument(session: Session, **payload: str) -> tuple[Instrument, bool]:
    existing = session.query(Instrument).filter(Instrument.symbol == payload["symbol"]).one_or_none()
    if existing is None:
        instrument = Instrument(**payload)
        session.add(instrument)
        session.flush()
        return instrument, True

    existing.name = payload["name"]
    existing.market = payload["market"]
    existing.asset_type = payload["asset_type"]
    existing.currency = payload["currency"]
    existing.timezone = payload["timezone"]
    existing.source_route = payload["source_route"]
    existing.is_active = True
    session.flush()
    return existing, False


def _ensure_watchlist(session: Session, *, name: str, description: str) -> tuple[Watchlist, bool]:
    existing = session.query(Watchlist).filter(Watchlist.name == name).one_or_none()
    if existing is not None:
        existing.description = description
        session.flush()
        return existing, False

    watchlist = create_watchlist(session, name=name, description=description)
    return watchlist, True


def _ensure_tag(session: Session, instrument_id: int, tag: str) -> int:
    existing = (
        session.query(InstrumentTag)
        .filter(InstrumentTag.instrument_id == instrument_id, InstrumentTag.tag == tag)
        .one_or_none()
    )
    if existing is not None:
        return 0
    add_tag_to_instrument(session, instrument_id=instrument_id, tag=tag)
    return 1


def _ensure_watchlist_item(session: Session, watchlist_id: int, instrument_id: int) -> None:
    existing = (
        session.query(WatchlistItem)
        .filter(
            WatchlistItem.watchlist_id == watchlist_id,
            WatchlistItem.instrument_id == instrument_id,
        )
        .one_or_none()
    )
    if existing is None:
        add_instrument_to_watchlist(session, watchlist_id=watchlist_id, instrument_id=instrument_id)


def _build_price_series(
    *,
    trade_date: date,
    start_price: Decimal,
    daily_step: Decimal,
    volume_base: int,
    market: str,
) -> list[dict[str, str | int]]:
    rows: list[dict[str, str | int]] = []
    current_close = start_price
    for index in range(30):
        current_date = trade_date - timedelta(days=29 - index)
        open_price = current_close - Decimal("1")
        high_price = current_close + Decimal("2")
        low_price = current_close - Decimal("2")
        change = current_close - open_price
        change_percent = ((change / open_price) * Decimal("100")).quantize(Decimal("0.0001"))
        rows.append(
            {
                "trade_date": current_date.isoformat(),
                "open": f"{open_price:.4f}",
                "high": f"{high_price:.4f}",
                "low": f"{low_price:.4f}",
                "close": f"{current_close:.4f}",
                "volume": volume_base + (index * 10_000),
                "turnover_value": f"{(current_close * Decimal(volume_base + (index * 10_000))):.4f}",
                "transactions_count": 1000 + index,
                "change": f"{change:.4f}",
                "change_percent": f"{change_percent:.4f}",
            }
        )
        current_close += daily_step if market == "TW" else daily_step + Decimal("0.3")
    return rows
