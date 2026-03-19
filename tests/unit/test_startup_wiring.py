import asyncio

from apps.api.main import create_app, lifespan


def test_app_lifespan_sets_startup_state() -> None:
    app = create_app()

    assert app.state.startup_complete is False
    assert app.state.settings.app_name == app.title

    async def run_lifespan() -> None:
        async with lifespan(app):
            assert app.state.startup_complete is True
            assert app.state.started_at is not None

    asyncio.run(run_lifespan())
