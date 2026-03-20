from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from services.core.bootstrap import seed_sample_reference_data
from services.core.market_data import clear_demo_workspace_data, has_any_daily_bars, run_real_twse_backfill
from services.connectors.twse import TwseDailyMarketDataConnector
from services.db.base import Base
from services.models import import_models
from services.models.backtest_run import BacktestRun
from services.models.backtest_trade import BacktestTrade
from services.models.candidate_item import CandidateItem
from services.models.candidate_run import CandidateRun
from services.models.daily_bar import DailyBar
from services.models.indicator_value import IndicatorValue
from services.models.instrument import Instrument
from services.models.report_daily import ReportDaily
from services.models.strategy import Strategy
from services.models.tw_derivatives_daily import TwDerivativesDaily
from services.models.tw_derivatives_feature import TwDerivativesFeature
from services.models.tw_institutional_spot_daily import TwInstitutionalSpotDaily
from services.schemas.etl import NormalizedDataBatch, NormalizedDailyBarRecord


def _build_session() -> Session:
    import_models()
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return session_factory()


class _FakeTwseConnector(TwseDailyMarketDataConnector):

    def fetch(self, request):
        return type("FetchResult", (), {"payload": {"data": [{"trade_date": request.trade_date.isoformat()}]}})

    def normalize(self, payload, request):
        trade_date = request.trade_date
        assert trade_date is not None
        assert request.symbol is not None
        return NormalizedDataBatch(
            daily_bars=[
                NormalizedDailyBarRecord(
                    instrument_id=request.instrument_id,
                    symbol=request.symbol,
                    market="TW",
                    currency="TWD",
                    source_route=request.source_route or self.source_route,
                    trade_date=trade_date,
                    open=Decimal("100"),
                    high=Decimal("102"),
                    low=Decimal("99"),
                    close=Decimal("101"),
                    volume=1000,
                    change=Decimal("1"),
                    change_percent=Decimal("1.0"),
                )
            ]
        )


def test_run_real_twse_backfill_loads_weekdays_only() -> None:
    session = _build_session()
    seed_sample_reference_data(session)

    result = run_real_twse_backfill(
        session,
        symbols=("2330",),
        start_date=date(2026, 3, 13),
        end_date=date(2026, 3, 17),
        connector=_FakeTwseConnector(),
    )

    instrument = session.query(Instrument).filter(Instrument.symbol == "2330").one()
    assert result.instruments_processed == 1
    assert result.trading_days_processed == 3
    assert result.daily_bars_loaded == 3
    assert session.query(DailyBar).filter(DailyBar.instrument_id == instrument.id).count() == 3


def test_has_any_daily_bars_detects_existing_range() -> None:
    session = _build_session()
    seed_sample_reference_data(session)
    instrument = session.query(Instrument).filter(Instrument.symbol == "2330").one()
    session.add(
        DailyBar(
            instrument_id=instrument.id,
            trade_date=date(2026, 3, 20),
            open=Decimal("100"),
            high=Decimal("102"),
            low=Decimal("99"),
            close=Decimal("101"),
            volume=1000,
        )
    )
    session.commit()

    assert has_any_daily_bars(
        session,
        instrument_id=instrument.id,
        start_date=date(2026, 3, 19),
        end_date=date(2026, 3, 20),
    )


def test_clear_demo_workspace_data_removes_sample_and_generated_demo_rows() -> None:
    session = _build_session()
    seed_sample_reference_data(session)
    instrument = session.query(Instrument).filter(Instrument.symbol == "2330").one()

    session.add(
        DailyBar(
            instrument_id=instrument.id,
            trade_date=date(2026, 3, 20),
            open=Decimal("100"),
            high=Decimal("102"),
            low=Decimal("99"),
            close=Decimal("101"),
            volume=1000,
        )
    )
    session.add(
        IndicatorValue(
            instrument_id=instrument.id,
            trade_date=date(2026, 3, 20),
            indicator_name="sma",
            component="value",
            parameter_signature="period=20",
            value=Decimal("100"),
        )
    )
    derivative = TwDerivativesDaily(
        trade_date=date(2026, 3, 20),
        market="futures",
        product_code="TX",
        product_name="TX",
        institution="foreign_investors",
        long_open_interest=10,
        short_open_interest=5,
        net_open_interest=5,
        long_amount=Decimal("100"),
        short_amount=Decimal("50"),
        net_amount=Decimal("50"),
        source_route="demo_seed",
        is_options=False,
    )
    session.add(derivative)
    session.flush()
    session.add(
        TwDerivativesFeature(
            daily_record_id=derivative.id,
            trade_date=date(2026, 3, 20),
            market="futures",
            product_code="TX",
            contract_period=None,
            institution="foreign_investors",
            call_put=None,
            delta_1d=Decimal("1"),
            delta_5d=Decimal("1"),
            delta_20d=Decimal("1"),
            zscore_20d=Decimal("1"),
            regime_label="bullish",
            bias_score=Decimal("1"),
            anomaly_flag=False,
        )
    )
    session.add(
        TwInstitutionalSpotDaily(
            trade_date=date(2026, 3, 20),
            market="TW",
            institution="foreign_investors",
            buy_amount=Decimal("100"),
            sell_amount=Decimal("90"),
            net_amount=Decimal("10"),
            source_route="demo_seed",
        )
    )
    candidate_run = CandidateRun(
        candidate_date=date(2026, 3, 20),
        status="completed",
        total_candidates=1,
        generation_config_json={},
        summary_json={},
    )
    session.add(candidate_run)
    session.flush()
    session.add(
        CandidateItem(
            run_id=candidate_run.id,
            instrument_id=instrument.id,
            candidate_date=date(2026, 3, 20),
            symbol="2330",
            score=Decimal("5"),
            rank=1,
            candidate_reasons_json=["demo"],
            supporting_metrics_json={},
        )
    )
    strategy = Strategy(name="Demo Time Exit Trend", description="Deterministic local demo backtest", definition_json={})
    session.add(strategy)
    session.flush()
    backtest_run = BacktestRun(
        strategy_id=strategy.id,
        status="completed",
        initial_cash=Decimal("100000"),
        final_cash=Decimal("110000"),
        total_return=Decimal("10000"),
        total_return_pct=Decimal("10"),
        total_trades=1,
        win_rate=Decimal("1"),
        fee_paid=Decimal("0"),
        tax_paid=Decimal("0"),
        slippage_paid=Decimal("0"),
        resolved_parameters_json={},
        metrics_json={},
        notes=None,
        started_at=datetime(2026, 3, 20, 9, 0, tzinfo=UTC),
        finished_at=datetime(2026, 3, 20, 13, 30, tzinfo=UTC),
    )
    session.add(backtest_run)
    session.flush()
    session.add(
        BacktestTrade(
            run_id=backtest_run.id,
            instrument_id=instrument.id,
            entry_date=date(2026, 3, 19),
            exit_date=date(2026, 3, 20),
            entry_price=Decimal("100"),
            exit_price=Decimal("101"),
            quantity=1,
            gross_pnl=Decimal("1"),
            net_pnl=Decimal("1"),
            fee_paid=Decimal("0"),
            tax_paid=Decimal("0"),
            slippage_paid=Decimal("0"),
            holding_period_days=1,
            exit_reason="time_exit",
        )
    )
    session.add(
        ReportDaily(
            report_date=date(2026, 3, 20),
            report_type="market_summary",
            report_key="",
            title="demo",
            content_json={},
            markdown_text="demo",
        )
    )
    session.commit()

    result = clear_demo_workspace_data(session)

    assert result.daily_bars_deleted == 1
    assert result.indicator_values_deleted == 1
    assert result.tw_derivatives_daily_deleted == 1
    assert result.tw_derivatives_features_deleted == 1
    assert result.tw_institutional_spot_deleted == 1
    assert result.candidate_runs_deleted == 1
    assert result.candidate_items_deleted == 1
    assert result.report_rows_deleted == 1
    assert result.backtest_runs_deleted == 1
    assert result.backtest_trades_deleted == 1
    assert session.query(DailyBar).count() == 0
    assert session.query(ReportDaily).count() == 0
