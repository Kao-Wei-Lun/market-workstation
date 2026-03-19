from fastapi import FastAPI

from apps.api.main import app, create_app


def test_app_imports_successfully() -> None:
    assert isinstance(app, FastAPI)
    assert isinstance(create_app(), FastAPI)
