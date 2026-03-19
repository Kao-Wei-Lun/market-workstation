from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from services.connectors.base import BaseConnector, ConnectorRequest, FetchResult, ProviderConnectorConfig
from services.core.etl.pipeline import run_ingestion_pipeline
from services.db.base import Base
from services.models import import_models
from services.models.daily_bar import DailyBar
from services.models.ingest_job import IngestJob
from services.schemas.etl import NormalizedDailyBarRecord, NormalizedDataBatch


class FakeDailyBarConnector(BaseConnector):
    source_route = "fake_daily_bars"

    def __init__(self) -> None:
        super().__init__(ProviderConnectorConfig(provider_name="fake"))

    def fetch(self, request: ConnectorRequest) -> FetchResult:
        return self._build_fetch_result({"ok": True})

    def normalize(self, payload: dict[str, object], request: ConnectorRequest) -> NormalizedDataBatch:
        return NormalizedDataBatch(
            daily_bars=[
                NormalizedDailyBarRecord(
                    instrument_id=1,
                    symbol="2330",
                    market="TW",
                    currency="TWD",
                    source_route=self.source_route,
                    trade_date=date(2024, 1, 2),
                    open=Decimal("520"),
                    high=Decimal("525"),
                    low=Decimal("518"),
                    close=Decimal("523"),
                    volume=12345,
                )
            ]
        )


def _build_session() -> Session:
    import_models()
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return session_factory()


def test_etl_pipeline_loads_data_and_marks_job_success() -> None:
    session = _build_session()

    result = run_ingestion_pipeline(
        session,
        connector=FakeDailyBarConnector(),
        request=ConnectorRequest(symbol="2330", trade_date=date(2024, 1, 2), instrument_id=1),
        job_type="daily_bar_sync",
    )

    jobs = session.query(IngestJob).all()
    bars = session.query(DailyBar).all()

    assert result.daily_bars_loaded == 1
    assert len(jobs) == 1
    assert jobs[0].status == "success"
    assert len(bars) == 1


def test_etl_pipeline_marks_job_failed_on_validation_error() -> None:
    class InvalidConnector(FakeDailyBarConnector):
        def normalize(self, payload: dict[str, object], request: ConnectorRequest) -> NormalizedDataBatch:
            record = NormalizedDailyBarRecord(
                instrument_id=1,
                symbol="2330",
                market="TW",
                currency="TWD",
                source_route=self.source_route,
                trade_date=date(2024, 1, 2),
                open=Decimal("520"),
                high=Decimal("525"),
                low=Decimal("518"),
                close=Decimal("523"),
                volume=-1,
            )
            return NormalizedDataBatch(daily_bars=[record, record])

    session = _build_session()

    try:
        run_ingestion_pipeline(
            session,
            connector=InvalidConnector(),
            request=ConnectorRequest(symbol="2330", trade_date=date(2024, 1, 2), instrument_id=1),
            job_type="daily_bar_sync",
        )
    except ValueError as exc:
        assert "duplicate daily bar" in str(exc)
    else:
        raise AssertionError("pipeline should have raised ValueError")

    jobs = session.query(IngestJob).all()
    assert len(jobs) == 1
    assert jobs[0].status == "failed"
