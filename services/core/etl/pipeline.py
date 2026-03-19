from __future__ import annotations

from sqlalchemy.orm import Session

from services.connectors.base import BaseConnector, ConnectorRequest
from services.core.etl.fetch import fetch_connector_payload
from services.core.etl.load import load_normalized_batch
from services.core.etl.normalize import normalize_connector_payload
from services.core.etl.validate import validate_normalized_batch
from services.core.ingest_jobs import record_job_failure, record_job_start, record_job_success
from services.schemas.etl import LoadResult


def run_ingestion_pipeline(
    session: Session,
    *,
    connector: BaseConnector,
    request: ConnectorRequest,
    job_type: str,
) -> LoadResult:
    job = record_job_start(
        session,
        source_route=request.source_route or connector.source_route,
        job_type=job_type,
        trade_date=request.trade_date,
    )
    try:
        fetch_result = fetch_connector_payload(connector, request)
        normalized = normalize_connector_payload(connector, fetch_result.payload, request)
        validation = validate_normalized_batch(normalized)
        if not validation.is_valid:
            msg = "; ".join(issue.message for issue in validation.issues)
            raise ValueError(msg)
        load_result = load_normalized_batch(session, normalized)
    except Exception as exc:
        record_job_failure(session, job, str(exc))
        raise

    record_job_success(session, job)
    return load_result
