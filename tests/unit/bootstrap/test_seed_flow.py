from __future__ import annotations

from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from services.core.bootstrap import DEFAULT_DEMO_TRADE_DATE, generate_demo_data, run_sample_daily_market_etl, seed_sample_reference_data
from services.core.derivatives.summary import get_latest_institutional_bias_summary
from services.db.base import Base
from services.models import import_models
from services.models.backtest_run import BacktestRun
from services.models.backtest_trade import BacktestTrade
from services.models.candidate_item import CandidateItem
from services.models.candidate_run import CandidateRun
from services.models.daily_bar import DailyBar
from services.models.instrument import Instrument
from services.models.instrument_tag import InstrumentTag
from services.models.report_daily import ReportDaily
from services.models.strategy import Strategy
from services.models.tw_derivatives_daily import TwDerivativesDaily
from services.models.tw_derivatives_feature import TwDerivativesFeature
from services.models.watchlist import Watchlist
from services.models.watchlist_item import WatchlistItem


def _build_session() -> Session:
    import_models()
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return session_factory()


def test_seed_sample_reference_data_is_idempotent() -> None:
    session = _build_session()

    first = seed_sample_reference_data(session)
    second = seed_sample_reference_data(session)

    assert first.instruments_created == 3
    assert second.instruments_created == 0
    assert session.query(Instrument).count() == 3
    assert session.query(Watchlist).count() == 1
    assert session.query(WatchlistItem).count() == 2
    assert session.query(InstrumentTag).count() == 5


def test_sample_etl_loads_seeded_daily_bars() -> None:
    session = _build_session()

    result = run_sample_daily_market_etl(session, trade_date=date(2024, 1, 31))

    assert result.instruments_processed == 2
    assert result.daily_bars_loaded == 60
    assert session.query(DailyBar).count() == 60


def test_generate_demo_data_is_idempotent_and_populates_frontend_visible_tables() -> None:
    session = _build_session()

    first = generate_demo_data(session, trade_date=DEFAULT_DEMO_TRADE_DATE)
    second = generate_demo_data(session, trade_date=DEFAULT_DEMO_TRADE_DATE)

    assert first.candidate_items_created > 0
    assert first.backtest_trades_created > 0
    assert first.reports_persisted > 0
    assert first.tw_derivatives_features_persisted > 0

    assert session.query(DailyBar).count() == 60
    assert session.query(CandidateRun).count() == 1
    assert session.query(CandidateItem).count() == second.candidate_items_created
    assert session.query(Strategy).count() == 1
    assert session.query(BacktestRun).count() == 1
    assert session.query(BacktestTrade).count() == second.backtest_trades_created
    assert session.query(TwDerivativesDaily).count() == 42
    assert session.query(TwDerivativesFeature).count() == 42
    assert session.query(ReportDaily).count() > 0

    latest_summary = get_latest_institutional_bias_summary(session)
    assert latest_summary is not None
    assert latest_summary.trade_date == DEFAULT_DEMO_TRADE_DATE
