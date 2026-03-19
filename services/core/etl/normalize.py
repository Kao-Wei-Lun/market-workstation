from services.connectors.base import BaseConnector, ConnectorRequest, JsonMapping
from services.schemas.etl import NormalizedDataBatch


def normalize_connector_payload(
    connector: BaseConnector,
    payload: JsonMapping,
    request: ConnectorRequest,
) -> NormalizedDataBatch:
    return connector.normalize(payload, request)
