from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI

from apps.api.routes.classification import router as classification_router
from apps.api.routes.backtests import router as backtests_router
from apps.api.routes.candidates import router as candidates_router
from apps.api.routes.dashboard import router as dashboard_router
from apps.api.routes.derivatives import router as derivatives_router
from apps.api.routes.health import router as health_router
from apps.api.routes.reports import router as reports_router
from config.settings import get_settings
from services.models import import_models


@asynccontextmanager
async def lifespan(app: FastAPI):
    import_models()
    app.state.started_at = datetime.now(tz=timezone.utc)
    app.state.startup_complete = True
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.startup_complete = False
    app.include_router(backtests_router)
    app.include_router(candidates_router)
    app.include_router(classification_router)
    app.include_router(dashboard_router)
    app.include_router(derivatives_router)
    app.include_router(reports_router)
    app.include_router(health_router)
    return app


app = create_app()
