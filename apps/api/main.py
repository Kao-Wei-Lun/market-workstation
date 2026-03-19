from fastapi import FastAPI

from apps.api.routes.classification import router as classification_router
from apps.api.routes.backtests import router as backtests_router
from apps.api.routes.health import router as health_router
from apps.api.routes.reports import router as reports_router
from config.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
    )
    app.include_router(backtests_router)
    app.include_router(classification_router)
    app.include_router(reports_router)
    app.include_router(health_router)
    return app


app = create_app()
