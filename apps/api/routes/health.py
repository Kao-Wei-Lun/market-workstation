from fastapi import APIRouter

from services.core.health import build_healthcheck_payload
from services.schemas.health import HealthcheckResponse

router = APIRouter(tags=["health"])


@router.get("/healthz", response_model=HealthcheckResponse)
async def healthcheck() -> HealthcheckResponse:
    return build_healthcheck_payload()


@router.get("/health", response_model=HealthcheckResponse)
async def healthcheck_alias() -> HealthcheckResponse:
    return build_healthcheck_payload()
