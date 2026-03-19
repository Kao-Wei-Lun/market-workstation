from config.settings import get_settings
from services.schemas.health import HealthcheckResponse


def build_healthcheck_payload() -> HealthcheckResponse:
    settings = get_settings()
    return HealthcheckResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.app_env,
        version=settings.app_version,
    )
