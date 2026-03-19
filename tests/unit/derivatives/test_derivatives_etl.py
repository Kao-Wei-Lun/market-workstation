from __future__ import annotations

from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from services.connectors.base import ConnectorRequest, FetchResult
from services.connectors.taifex import TaifexInstitutionalDailyConnector
from services.core.derivatives.etl import run_taifex_derivatives_ingestion
from services.db.base import Base
from services.models import import_models
from services.models.ingest_job import IngestJob
from services.models.tw_derivatives_daily import TwDerivativesDaily
from services.schemas.etl import NormalizedDataBatch, NormalizedTwDerivativesDailyRecord


class FakeTaifexConnector(TaifexInstitutionalDailyConnector):
    def fetch(self, request: ConnectorRequest) -> FetchResult:
        return self._build_fetch_result({"ok": True})

    def normalize(self, payload: dict[str, object], request: ConnectorRequest) -> NormalizedDataBatch:
        return NormalizedDataBatch(
            tw_derivatives_daily=[
                NormalizedTwDerivativesDailyRecord(
                    trade_date=date(2024, 1, 2),
                    market="futures",
                    product_code="TX",
                    product_name="臺股期貨",
                    contract_period="202401",
                    institution="foreign_investors",
                    long_open_interest=12000,
                    short_open_interest=10000,
                    net_open_interest=2000,
                    source_route=self.source_route,
                )
            ]
        )


def _build_session() -> Session:
    import_models()
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return session_factory()


def test_derivatives_etl_loads_daily_rows_and_marks_job_success() -> None:
    session = _build_session()

    result = run_taifex_derivatives_ingestion(
        session,
        request=ConnectorRequest(trade_date=date(2024, 1, 2)),
        connector=FakeTaifexConnector(),
    )

    daily_rows = session.query(TwDerivativesDaily).all()
    jobs = session.query(IngestJob).all()

    assert result.tw_derivatives_daily_loaded == 1
    assert len(daily_rows) == 1
    assert daily_rows[0].net_open_interest == 2000
    assert jobs[0].status == "success"
