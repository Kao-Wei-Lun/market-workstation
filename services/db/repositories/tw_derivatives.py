from __future__ import annotations

from sqlalchemy.orm import Session

from services.models.tw_derivatives_daily import TwDerivativesDaily
from services.models.tw_derivatives_feature import TwDerivativesFeature
from services.schemas.etl import NormalizedTwDerivativesDailyRecord


class TwDerivativesDailyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_many(self, records: list[NormalizedTwDerivativesDailyRecord]) -> int:
        if not records:
            return 0

        loaded = 0
        for record in records:
            existing = (
                self.session.query(TwDerivativesDaily)
                .filter(
                    TwDerivativesDaily.trade_date == record.trade_date,
                    TwDerivativesDaily.market == record.market,
                    TwDerivativesDaily.product_code == record.product_code,
                    TwDerivativesDaily.institution == record.institution,
                    TwDerivativesDaily.contract_period == record.contract_period,
                    TwDerivativesDaily.call_put == record.call_put,
                )
                .one_or_none()
            )

            if existing is None:
                self.session.add(
                    TwDerivativesDaily(
                        trade_date=record.trade_date,
                        market=record.market,
                        product_code=record.product_code,
                        product_name=record.product_name,
                        contract_period=record.contract_period,
                        institution=record.institution,
                        call_put=record.call_put,
                        long_open_interest=record.long_open_interest,
                        short_open_interest=record.short_open_interest,
                        net_open_interest=record.net_open_interest,
                        long_amount=record.long_amount,
                        short_amount=record.short_amount,
                        net_amount=record.net_amount,
                        source_route=record.source_route,
                        is_options=record.is_options,
                    )
                )
            else:
                existing.product_name = record.product_name
                existing.contract_period = record.contract_period
                existing.call_put = record.call_put
                existing.long_open_interest = record.long_open_interest
                existing.short_open_interest = record.short_open_interest
                existing.net_open_interest = record.net_open_interest
                existing.long_amount = record.long_amount
                existing.short_amount = record.short_amount
                existing.net_amount = record.net_amount
                existing.source_route = record.source_route
                existing.is_options = record.is_options
            loaded += 1

        self.session.flush()
        return loaded


class TwDerivativesFeatureRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def replace_many(self, records: list[TwDerivativesFeature]) -> int:
        if not records:
            return 0

        loaded = 0
        for record in records:
            existing = (
                self.session.query(TwDerivativesFeature)
                .filter(TwDerivativesFeature.daily_record_id == record.daily_record_id)
                .one_or_none()
            )
            if existing is None:
                self.session.add(record)
            else:
                existing.trade_date = record.trade_date
                existing.market = record.market
                existing.product_code = record.product_code
                existing.contract_period = record.contract_period
                existing.institution = record.institution
                existing.call_put = record.call_put
                existing.delta_1d = record.delta_1d
                existing.delta_5d = record.delta_5d
                existing.delta_20d = record.delta_20d
                existing.zscore_20d = record.zscore_20d
                existing.regime_label = record.regime_label
                existing.bias_score = record.bias_score
                existing.anomaly_flag = record.anomaly_flag
            loaded += 1

        self.session.flush()
        return loaded
