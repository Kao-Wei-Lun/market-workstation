from services.connectors.base import BaseConnector, ConnectorRequest, FetchResult


def fetch_connector_payload(connector: BaseConnector, request: ConnectorRequest) -> FetchResult:
    return connector.fetch(request)
