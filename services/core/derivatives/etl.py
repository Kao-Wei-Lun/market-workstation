from __future__ import annotations

from sqlalchemy.orm import Session

from services.connectors.base import ConnectorRequest
from services.connectors.taifex import TaifexInstitutionalDailyConnector
from services.core.etl.pipeline import run_ingestion_pipeline
from services.schemas.etl import LoadResult


def run_taifex_derivatives_ingestion(
    session: Session,
    *,
    request: ConnectorRequest,
    connector: TaifexInstitutionalDailyConnector | None = None,
) -> LoadResult:
    return run_ingestion_pipeline(
        session,
        connector=connector or TaifexInstitutionalDailyConnector(),
        request=request,
        job_type="tw_derivatives_daily_sync",
    )
