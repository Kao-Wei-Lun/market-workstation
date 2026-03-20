from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from apps.api.main import app
from services.db.base import Base
from services.db.session import get_db_session
from services.models import import_models
from services.models.daily_bar import DailyBar
from services.models.indicator_value import IndicatorValue
from services.models.instrument import Instrument
from services.models.tw_derivatives_daily import TwDerivativesDaily
from services.models.tw_derivatives_feature import TwDerivativesFeature
from services.models.tw_institutional_spot_daily import TwInstitutionalSpotDaily


def _build_session() -> Session:
    import_models()
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return session_factory()


def _seed_chart_data(session: Session) -> None:
    trade_date = date(2024, 2, 5)
    index = Instrument(
        symbol="^TWII",
        name="TAIEX",
        market="TW",
        asset_type="index",
        currency="TWD",
        timezone="Asia/Taipei",
        source_route="demo_seed",
    )
    stock = Instrument(
        symbol="2330",
        name="TSMC",
        market="TW",
        asset_type="equity",
        currency="TWD",
        timezone="Asia/Taipei",
        source_route="demo_seed",
    )
    session.add_all([index, stock])
    session.flush()

    for offset, close in enumerate([18000, 18120, 18230, 18180, 18310]):
        current_date = trade_date - timedelta(days=4 - offset)
        for instrument in (index, stock):
            session.add(
                DailyBar(
                    instrument_id=instrument.id,
                    trade_date=current_date,
                    open=Decimal(str(close - 30)),
                    high=Decimal(str(close + 40)),
                    low=Decimal(str(close - 80)),
                    close=Decimal(str(close)),
                    volume=1000 + offset * 100,
                    change_percent=Decimal("1.25"),
                )
            )
            session.add(
                IndicatorValue(
                    instrument_id=instrument.id,
                    trade_date=current_date,
                    indicator_name="sma",
                    component="value",
                    parameter_signature="period=20",
                    value=Decimal(str(close - 50)),
                )
            )

    derivative_daily = TwDerivativesDaily(
        trade_date=trade_date,
        market="TAIFEX",
        product_code="TX",
        product_name="TAIEX Futures",
        contract_period="202402",
        institution="foreign_investors",
        call_put=None,
        long_open_interest=1200,
        short_open_interest=900,
        net_open_interest=300,
        long_amount=Decimal("1500000"),
        short_amount=Decimal("900000"),
        net_amount=Decimal("600000"),
        source_route="taifex_demo",
        is_options=False,
    )
    derivative_option = TwDerivativesDaily(
        trade_date=trade_date,
        market="TAIFEX",
        product_code="TXO",
        product_name="TAIEX Options",
        contract_period="202402",
        institution="foreign_investors",
        call_put="call",
        long_open_interest=800,
        short_open_interest=500,
        net_open_interest=300,
        long_amount=Decimal("700000"),
        short_amount=Decimal("300000"),
        net_amount=Decimal("400000"),
        source_route="taifex_demo",
        is_options=True,
    )
    session.add_all([derivative_daily, derivative_option])
    session.flush()
    session.add_all(
        [
            TwDerivativesFeature(
                daily_record_id=derivative_daily.id,
                trade_date=trade_date,
                market="TAIFEX",
                product_code="TX",
                contract_period="202402",
                institution="foreign_investors",
                call_put=None,
                delta_1d=Decimal("10"),
                delta_5d=Decimal("15"),
                delta_20d=Decimal("20"),
                zscore_20d=Decimal("1.2"),
                regime_label="bullish",
                bias_score=Decimal("1.5"),
                anomaly_flag=False,
            ),
            TwDerivativesFeature(
                daily_record_id=derivative_option.id,
                trade_date=trade_date,
                market="TAIFEX",
                product_code="TXO",
                contract_period="202402",
                institution="foreign_investors",
                call_put="call",
                delta_1d=Decimal("8"),
                delta_5d=Decimal("12"),
                delta_20d=Decimal("16"),
                zscore_20d=Decimal("0.9"),
                regime_label="bullish",
                bias_score=Decimal("1.1"),
                anomaly_flag=False,
            ),
        ]
    )
    session.add(
        TwInstitutionalSpotDaily(
            trade_date=trade_date,
            market="TW",
            institution="foreign_investors",
            buy_amount=Decimal("3000000000"),
            sell_amount=Decimal("2500000000"),
            net_amount=Decimal("500000000"),
            source_route="demo_seed",
        )
    )
    session.commit()


@pytest.mark.asyncio
async def test_chart_api_returns_ohlcv_indicators_and_annotations() -> None:
    session = _build_session()
    _seed_chart_data(session)

    async def override_db():
        yield session

    app.dependency_overrides[get_db_session] = override_db
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        instruments_response = await client.get("/api/charts/instruments", params={"market": "TW", "limit": 10})
        chart_response = await client.get("/api/charts/ohlcv/2330", params={"indicator_name": ["sma"]})
        create_annotation_response = await client.post(
            "/api/charts/annotations",
            json={
                "symbol": "2330",
                "view_kind": "instrument",
                "annotation_type": "range_box",
                "label": "整理區",
                "payload_json": {
                    "start_date": "2024-02-01",
                    "start_price": 18050,
                    "end_date": "2024-02-05",
                    "end_price": 18320,
                },
            },
        )
        annotated_chart_response = await client.get("/api/charts/ohlcv/2330", params={"indicator_name": ["sma"]})
        list_annotations_response = await client.get("/api/charts/annotations/2330", params={"view_kind": "instrument"})
        clear_response = await client.delete("/api/charts/annotations/clear/2330", params={"view_kind": "instrument"})

    app.dependency_overrides.clear()

    assert instruments_response.status_code == 200
    assert len(instruments_response.json()) >= 2
    assert chart_response.status_code == 200
    assert len(chart_response.json()["candles"]) == 5
    assert chart_response.json()["available_indicator_keys"] == ["sma"]
    assert create_annotation_response.status_code == 200
    assert create_annotation_response.json()["annotation_type"] == "range_box"
    assert annotated_chart_response.status_code == 200
    assert len(annotated_chart_response.json()["annotations"]) == 1
    assert list_annotations_response.status_code == 200
    assert list_annotations_response.json()[0]["annotation_type"] == "range_box"
    assert clear_response.status_code == 200
    assert clear_response.json()["deleted"] == 1


@pytest.mark.asyncio
async def test_chart_annotation_api_validates_required_payload_fields() -> None:
    session = _build_session()
    _seed_chart_data(session)

    async def override_db():
        yield session

    app.dependency_overrides[get_db_session] = override_db
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/charts/annotations",
            json={
                "symbol": "2330",
                "view_kind": "instrument",
                "annotation_type": "point_marker",
                "label": "漏資料",
                "payload_json": {"trade_date": "2024-02-05"},
            },
        )

    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert "payload missing required keys" in response.json()["detail"]


@pytest.mark.asyncio
async def test_institutional_flow_chart_api_returns_combined_daily_view() -> None:
    session = _build_session()
    _seed_chart_data(session)

    async def override_db():
        yield session

    app.dependency_overrides[get_db_session] = override_db
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/charts/institutional-flow/^TWII")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["instrument"]["symbol"] == "^TWII"
    assert len(payload["candles"]) == 5
    assert len(payload["flow_points"]) == 5
    assert payload["flow_points"][-1]["futures_net_open_interest"] == 300
    assert payload["flow_points"][-1]["options_net_open_interest"] == 300
    assert payload["flow_points"][-1]["spot_net_amount"] == "500000000.0000"


@pytest.mark.asyncio
async def test_market_structure_chart_api_returns_summary_and_series() -> None:
    session = _build_session()
    _seed_chart_data(session)

    async def override_db():
        yield session

    app.dependency_overrides[get_db_session] = override_db
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/charts/market-structure/^TWII")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["instrument"]["symbol"] == "^TWII"
    assert payload["summary"]["overall_regime"] == "bullish"
    assert "spot_net_amount" in payload["available_series"]
    assert payload["flow_points"][-1]["spot_net_amount"] == "500000000.0000"
