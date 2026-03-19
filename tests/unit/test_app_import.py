from fastapi import FastAPI

from apps.api.main import app, create_app
from config.settings import get_settings


def test_app_imports_successfully() -> None:
    assert isinstance(app, FastAPI)
    assert isinstance(create_app(), FastAPI)


def test_app_uses_configured_metadata() -> None:
    settings = get_settings()

    assert app.title == settings.app_name
    assert app.version == settings.app_version
