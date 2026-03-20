from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from config.universe import filter_universe_preset_by_scope, list_available_universe_presets, load_universe_preset
from services.core.backtesting.service import create_and_run_backtest
from services.core.candidates.service import generate_and_persist_candidate_run
from services.connectors.base import ConnectorRequest
from services.connectors.dev_seed import StaticDailyBarConnector
from services.core.classification.tags import add_tag_to_instrument
from services.core.classification.watchlists import add_instrument_to_watchlist, create_watchlist
from services.core.derivatives.features import compute_tw_derivatives_features
from services.core.etl.pipeline import run_ingestion_pipeline
from services.core.market_data import has_any_daily_bars
from services.db.repositories.tw_derivatives import TwDerivativesDailyRepository, TwDerivativesFeatureRepository
from services.db.repositories.tw_institutional_spot import TwInstitutionalSpotDailyRepository
from services.models.backtest_run import BacktestRun
from services.models.backtest_trade import BacktestTrade
from services.models.candidate_item import CandidateItem
from services.models.candidate_run import CandidateRun
from services.models.instrument import Instrument
from services.models.instrument_tag import InstrumentTag
from services.models.strategy import Strategy
from services.models.tw_derivatives_daily import TwDerivativesDaily
from services.models.watchlist import Watchlist
from services.models.watchlist_item import WatchlistItem
from services.schemas.backtesting import BacktestCreateRequest
from services.schemas.etl import NormalizedTwDerivativesDailyRecord
from workers.shared.jobs import run_daily_report_generation_job, run_indicator_update_job

SAMPLE_UNIVERSE_PRESET = "sample_reference"
DEFAULT_V1_UNIVERSE_PRESET = "v1_market_expanded"
SAMPLE_UNIVERSE = load_universe_preset(SAMPLE_UNIVERSE_PRESET)
SAMPLE_INSTRUMENT_SYMBOLS = {item.symbol for item in SAMPLE_UNIVERSE.instruments}
DEFAULT_DEMO_TRADE_DATE = date(2026, 3, 20)
DEMO_BACKTEST_NAME = "Demo Time Exit Trend"
DEMO_BACKTEST_DESCRIPTION = "Deterministic local demo backtest"


@dataclass(frozen=True)
class SeedResult:
    instruments_created: int
    watchlists_created: int
    tags_created: int


@dataclass(frozen=True)
class SampleEtlResult:
    instruments_processed: int
    daily_bars_loaded: int


@dataclass(frozen=True)
class UniverseLoadResult:
    preset_name: str
    description: str
    requested_scope_keys: tuple[str, ...]
    scopes_declared: int
    instruments_created: int
    instruments_updated: int
    tags_created: int
    watchlists_created: int
    watchlist_items_added: int
    total_instruments: int
    available_presets: tuple[str, ...]


@dataclass(frozen=True)
class DemoDataResult:
    trade_date: date
    instruments_created: int
    watchlists_created: int
    tags_created: int
    daily_bars_loaded: int
    indicator_values_persisted: int
    tw_derivatives_daily_loaded: int
    tw_derivatives_features_persisted: int
    tw_institutional_spot_loaded: int
    candidate_runs_created: int
    candidate_items_created: int
    backtest_runs_created: int
    backtest_trades_created: int
    reports_persisted: int


def seed_sample_reference_data(session: Session) -> SeedResult:
    result = load_instrument_universe(session, preset_name=SAMPLE_UNIVERSE_PRESET)
    return SeedResult(
        instruments_created=result.instruments_created,
        watchlists_created=result.watchlists_created,
        tags_created=result.tags_created,
    )


def load_instrument_universe(
    session: Session,
    *,
    preset_name: str = DEFAULT_V1_UNIVERSE_PRESET,
    include_watchlists: bool = True,
    scope_keys: tuple[str, ...] = (),
) -> UniverseLoadResult:
    preset = filter_universe_preset_by_scope(load_universe_preset(preset_name), scope_keys)

    instruments_created = 0
    instruments_updated = 0
    tags_created = 0
    watchlists_created = 0
    watchlist_items_added = 0
    symbol_to_instrument_id: dict[str, int] = {}

    for definition in preset.instruments:
        instrument, created = _upsert_instrument(
            session,
            symbol=definition.symbol,
            name=definition.name,
            market=definition.market,
            asset_type=definition.asset_type,
            currency=definition.currency,
            timezone=definition.timezone,
            source_route=definition.source_route,
        )
        instruments_created += int(created)
        instruments_updated += int(not created)
        symbol_to_instrument_id[definition.symbol] = instrument.id
        for tag in definition.tags:
            tags_created += _ensure_tag(session, instrument.id, tag)

    if include_watchlists:
        for watchlist_definition in preset.watchlists:
            watchlist, created = _ensure_watchlist(
                session,
                name=watchlist_definition.name,
                description=watchlist_definition.description,
            )
            watchlists_created += int(created)
            for symbol in watchlist_definition.symbols:
                instrument_id = symbol_to_instrument_id.get(symbol)
                if instrument_id is None:
                    continue
                watchlist_items_added += _ensure_watchlist_item(session, watchlist.id, instrument_id)

    session.commit()
    return UniverseLoadResult(
        preset_name=preset.preset_name,
        description=preset.description,
        requested_scope_keys=scope_keys,
        scopes_declared=len(preset.scopes),
        instruments_created=instruments_created,
        instruments_updated=instruments_updated,
        tags_created=tags_created,
        watchlists_created=watchlists_created,
        watchlist_items_added=watchlist_items_added,
        total_instruments=len(preset.instruments),
        available_presets=tuple(list_available_universe_presets()),
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
        "^TWII": _build_price_series(
            trade_date=trade_date,
            start_price=Decimal("21800"),
            daily_step=Decimal("45"),
            volume_base=3_200_000,
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
        series_start_date = date.fromisoformat(str(rows[0]["trade_date"]))
        series_end_date = date.fromisoformat(str(rows[-1]["trade_date"]))
        if has_any_daily_bars(
            session,
            instrument_id=instrument.id,
            start_date=series_start_date,
            end_date=series_end_date,
        ):
            instruments_processed += 1
            continue
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


def generate_demo_data(session: Session, *, trade_date: date = DEFAULT_DEMO_TRADE_DATE) -> DemoDataResult:
    seed_result = seed_sample_reference_data(session)
    etl_result = run_sample_daily_market_etl(session, trade_date=trade_date)

    indicator_result = run_indicator_update_job(session, trade_date)
    derivatives_daily_loaded, derivatives_features_persisted, spot_loaded = _seed_demo_derivatives_data(
        session,
        trade_date=trade_date,
    )

    _delete_existing_demo_candidate_runs(session, candidate_date=trade_date)
    candidate_run, candidate_items = generate_and_persist_candidate_run(session, candidate_date=trade_date, top_n=10)

    _delete_existing_demo_backtests(session)
    _strategy, backtest_run = create_and_run_backtest(session, _build_demo_backtest_request(session))
    session.commit()
    backtest_run_id = backtest_run.id
    backtest_trade_count = (
        session.query(BacktestTrade)
        .filter(BacktestTrade.run_id == backtest_run_id)
        .count()
    )

    report_result = run_daily_report_generation_job(session, trade_date)

    return DemoDataResult(
        trade_date=trade_date,
        instruments_created=seed_result.instruments_created,
        watchlists_created=seed_result.watchlists_created,
        tags_created=seed_result.tags_created,
        daily_bars_loaded=etl_result.daily_bars_loaded,
        indicator_values_persisted=indicator_result.metrics.get("indicator_values_persisted", 0),
        tw_derivatives_daily_loaded=derivatives_daily_loaded,
        tw_derivatives_features_persisted=derivatives_features_persisted,
        tw_institutional_spot_loaded=spot_loaded,
        candidate_runs_created=int(candidate_run.id > 0),
        candidate_items_created=len(candidate_items),
        backtest_runs_created=int(backtest_run_id > 0),
        backtest_trades_created=backtest_trade_count,
        reports_persisted=report_result.metrics.get("reports_persisted", 0),
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


def _ensure_watchlist_item(session: Session, watchlist_id: int, instrument_id: int) -> int:
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
        return 1
    return 0


def _build_price_series(
    *,
    trade_date: date,
    start_price: Decimal,
    daily_step: Decimal,
    volume_base: int,
    market: str,
) -> list[dict[str, str | int]]:
    rows: list[dict[str, str | int]] = []
    previous_close = start_price - (daily_step * Decimal("0.6"))
    trading_dates = _build_trading_dates(trade_date, periods=30)
    drift_pattern = _build_drift_pattern(market)
    gap_pattern = [Decimal("-0.15"), Decimal("0.10"), Decimal("-0.05"), Decimal("0.18"), Decimal("-0.12")]
    upper_wick_pattern = [Decimal("0.55"), Decimal("0.75"), Decimal("0.48"), Decimal("0.68"), Decimal("0.60")]
    lower_wick_pattern = [Decimal("0.45"), Decimal("0.62"), Decimal("0.58"), Decimal("0.40"), Decimal("0.70")]
    volume_pattern = [0, 180_000, -120_000, 260_000, 90_000, -80_000, 210_000, -150_000]
    for index, current_date in enumerate(trading_dates):
        daily_drift = daily_step * drift_pattern[index % len(drift_pattern)]
        close_price = previous_close + daily_drift
        open_price = previous_close + (daily_step * gap_pattern[index % len(gap_pattern)])
        high_price = max(open_price, close_price) + (daily_step * upper_wick_pattern[index % len(upper_wick_pattern)])
        low_price = min(open_price, close_price) - (daily_step * lower_wick_pattern[index % len(lower_wick_pattern)])
        change = close_price - previous_close
        change_percent = ((change / previous_close) * Decimal("100")).quantize(Decimal("0.0001"))
        volume = max(100_000, volume_base + volume_pattern[index % len(volume_pattern)] + (index * 6_500))
        rows.append(
            {
                "trade_date": current_date.isoformat(),
                "open": f"{open_price:.4f}",
                "high": f"{high_price:.4f}",
                "low": f"{low_price:.4f}",
                "close": f"{close_price:.4f}",
                "volume": volume,
                "turnover_value": f"{(((open_price + high_price + low_price + close_price) / Decimal('4')) * Decimal(volume)):.4f}",
                "transactions_count": 900 + (index * 14) + (index % 4) * 7,
                "change": f"{change:.4f}",
                "change_percent": f"{change_percent:.4f}",
            }
        )
        previous_close = close_price
    return rows


def _build_trading_dates(trade_date: date, *, periods: int) -> list[date]:
    dates: list[date] = []
    current_date = trade_date
    while len(dates) < periods:
        if current_date.weekday() < 5:
            dates.append(current_date)
        current_date -= timedelta(days=1)
    return list(reversed(dates))


def _build_drift_pattern(market: str) -> list[Decimal]:
    if market == "TW":
        return [
            Decimal("0.35"),
            Decimal("-0.28"),
            Decimal("0.62"),
            Decimal("0.18"),
            Decimal("-0.55"),
            Decimal("0.92"),
            Decimal("0.24"),
            Decimal("-0.38"),
            Decimal("0.58"),
            Decimal("0.12"),
        ]
    return [
        Decimal("0.22"),
        Decimal("-0.18"),
        Decimal("0.46"),
        Decimal("0.08"),
        Decimal("-0.34"),
        Decimal("0.64"),
        Decimal("0.19"),
        Decimal("-0.27"),
        Decimal("0.41"),
        Decimal("0.06"),
    ]


def _seed_demo_derivatives_data(session: Session, *, trade_date: date) -> tuple[int, int, int]:
    records: list[NormalizedTwDerivativesDailyRecord] = []
    spot_loaded = 0
    spot_repository = TwInstitutionalSpotDailyRepository(session)
    trading_dates = _build_trading_dates(trade_date, periods=21)
    futures_pattern = [
        -160,
        -120,
        -70,
        -20,
        40,
        95,
        150,
        210,
        260,
        310,
        285,
        230,
        180,
        120,
        65,
        140,
        220,
        305,
        260,
        190,
        245,
    ]
    call_pattern = [
        35,
        20,
        10,
        30,
        55,
        72,
        88,
        96,
        108,
        124,
        112,
        85,
        64,
        42,
        18,
        52,
        78,
        102,
        89,
        71,
        95,
    ]
    put_pattern = [
        -48,
        -62,
        -75,
        -58,
        -35,
        -16,
        6,
        18,
        26,
        34,
        12,
        -14,
        -28,
        -37,
        -52,
        -24,
        8,
        22,
        16,
        -6,
        12,
    ]
    spot_pattern = [
        Decimal("-1800000000"),
        Decimal("-1320000000"),
        Decimal("-940000000"),
        Decimal("-520000000"),
        Decimal("-160000000"),
        Decimal("240000000"),
        Decimal("620000000"),
        Decimal("980000000"),
        Decimal("1340000000"),
        Decimal("1680000000"),
        Decimal("1420000000"),
        Decimal("960000000"),
        Decimal("540000000"),
        Decimal("160000000"),
        Decimal("-220000000"),
        Decimal("420000000"),
        Decimal("980000000"),
        Decimal("1560000000"),
        Decimal("1240000000"),
        Decimal("760000000"),
        Decimal("1180000000"),
    ]
    for index, current_date in enumerate(trading_dates):
        foreign_net = futures_pattern[index]
        foreign_options_call_net = call_pattern[index]
        foreign_options_put_net = put_pattern[index]
        spot_net = spot_pattern[index]
        spot_buy = Decimal("2800000000") + (Decimal(index % 5) * Decimal("140000000"))
        spot_sell = spot_buy - spot_net
        spot_repository.upsert(
            trade_date=current_date,
            market="TW",
            institution="foreign_investors",
            buy_amount=spot_buy,
            sell_amount=spot_sell,
            net_amount=spot_net,
            source_route="demo_seed",
        )
        spot_loaded += 1
        records.extend(
            [
                NormalizedTwDerivativesDailyRecord(
                    trade_date=current_date,
                    market="TAIFEX",
                    product_code="TX",
                    product_name="TAIEX Futures",
                    contract_period=trade_date.strftime("%Y%m"),
                    institution="foreign_investors",
                    call_put=None,
                    long_open_interest=1_000 + (index * 25),
                    short_open_interest=820 + (index * 7),
                    net_open_interest=foreign_net,
                    long_amount=Decimal("1200000") + (Decimal(index) * Decimal("25000")),
                    short_amount=Decimal("940000") + (Decimal(index) * Decimal("9000")),
                    net_amount=Decimal(foreign_net) * Decimal("1000"),
                    source_route="demo_seed",
                    is_options=False,
                ),
                NormalizedTwDerivativesDailyRecord(
                    trade_date=current_date,
                    market="TAIFEX",
                    product_code="TXO",
                    product_name="TAIEX Options",
                    contract_period=trade_date.strftime("%Y%m"),
                    institution="foreign_investors",
                    call_put="call",
                    long_open_interest=520 + (index * 11),
                    short_open_interest=430 + (index * 4),
                    net_open_interest=foreign_options_call_net,
                    long_amount=Decimal("340000") + (Decimal(index) * Decimal("7000")),
                    short_amount=Decimal("260000") + (Decimal(index) * Decimal("3000")),
                    net_amount=Decimal(foreign_options_call_net) * Decimal("850"),
                    source_route="demo_seed",
                    is_options=True,
                ),
                NormalizedTwDerivativesDailyRecord(
                    trade_date=current_date,
                    market="TAIFEX",
                    product_code="TXO",
                    product_name="TAIEX Options",
                    contract_period=trade_date.strftime("%Y%m"),
                    institution="foreign_investors",
                    call_put="put",
                    long_open_interest=390 + (index * 5),
                    short_open_interest=460 + index,
                    net_open_interest=foreign_options_put_net,
                    long_amount=Decimal("255000") + (Decimal(index) * Decimal("2500")),
                    short_amount=Decimal("315000") + (Decimal(index) * Decimal("4500")),
                    net_amount=Decimal(foreign_options_put_net) * Decimal("780"),
                    source_route="demo_seed",
                    is_options=True,
                ),
            ]
        )

    daily_loaded = TwDerivativesDailyRepository(session).upsert_many(records)
    session.flush()
    all_records = (
        session.query(TwDerivativesDaily)
        .filter(TwDerivativesDaily.trade_date <= trade_date, TwDerivativesDaily.source_route == "demo_seed")
        .order_by(TwDerivativesDaily.trade_date.asc(), TwDerivativesDaily.id.asc())
        .all()
    )
    features = compute_tw_derivatives_features(all_records)
    features_persisted = TwDerivativesFeatureRepository(session).replace_many(features)
    session.commit()
    return daily_loaded, features_persisted, spot_loaded


def _delete_existing_demo_candidate_runs(session: Session, *, candidate_date: date) -> None:
    run_ids = [
        run_id
        for (run_id,) in session.query(CandidateRun.id).filter(CandidateRun.candidate_date == candidate_date).all()
    ]
    if run_ids:
        session.query(CandidateItem).filter(CandidateItem.run_id.in_(run_ids)).delete(synchronize_session=False)
        session.query(CandidateRun).filter(CandidateRun.id.in_(run_ids)).delete(synchronize_session=False)
        session.commit()


def _delete_existing_demo_backtests(session: Session) -> None:
    strategy_ids = [
        strategy_id
        for (strategy_id,) in session.query(Strategy.id).filter(Strategy.name == DEMO_BACKTEST_NAME).all()
    ]
    if not strategy_ids:
        return
    run_ids = [
        run_id
        for (run_id,) in session.query(BacktestRun.id).filter(BacktestRun.strategy_id.in_(strategy_ids)).all()
    ]
    if run_ids:
        session.query(BacktestTrade).filter(BacktestTrade.run_id.in_(run_ids)).delete(synchronize_session=False)
        session.query(BacktestRun).filter(BacktestRun.id.in_(run_ids)).delete(synchronize_session=False)
    session.query(Strategy).filter(Strategy.id.in_(strategy_ids)).delete(synchronize_session=False)
    session.commit()


def _build_demo_backtest_request(session: Session) -> BacktestCreateRequest:
    instrument = session.query(Instrument).filter(Instrument.symbol == "2330").one()
    return BacktestCreateRequest.model_validate(
        {
            "name": DEMO_BACKTEST_NAME,
            "description": DEMO_BACKTEST_DESCRIPTION,
            "definition": {
                "instrument_id": instrument.id,
                "initial_cash": "100000",
                "position_size": "0.5",
                "time_exit_days": 5,
                "costs": {"fee_rate": "0.0005", "tax_rate": "0", "slippage_rate": "0.0005"},
                "entry_rule": {
                    "left": {"kind": "price", "field": "close"},
                    "operator": "gt",
                    "right": {"kind": "constant", "value": "0"},
                },
                "exit_rule": {
                    "left": {"kind": "price", "field": "close"},
                    "operator": "lt",
                    "right": {"kind": "constant", "value": "0"},
                },
            },
        }
    )
