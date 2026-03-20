from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from services.models.tw_institutional_spot_daily import TwInstitutionalSpotDaily


class TwInstitutionalSpotDailyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert(
        self,
        *,
        trade_date: date,
        market: str,
        institution: str,
        buy_amount: Decimal,
        sell_amount: Decimal,
        net_amount: Decimal,
        source_route: str,
    ) -> TwInstitutionalSpotDaily:
        existing = (
            self.session.query(TwInstitutionalSpotDaily)
            .filter(
                TwInstitutionalSpotDaily.trade_date == trade_date,
                TwInstitutionalSpotDaily.market == market,
                TwInstitutionalSpotDaily.institution == institution,
            )
            .one_or_none()
        )
        if existing is None:
            existing = TwInstitutionalSpotDaily(
                trade_date=trade_date,
                market=market,
                institution=institution,
                buy_amount=buy_amount,
                sell_amount=sell_amount,
                net_amount=net_amount,
                source_route=source_route,
            )
            self.session.add(existing)
        else:
            existing.buy_amount = buy_amount
            existing.sell_amount = sell_amount
            existing.net_amount = net_amount
            existing.source_route = source_route
        self.session.flush()
        return existing

    def list_for_market(
        self,
        *,
        market: str,
        institution: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[TwInstitutionalSpotDaily]:
        query = self.session.query(TwInstitutionalSpotDaily).filter(
            TwInstitutionalSpotDaily.market == market,
            TwInstitutionalSpotDaily.institution == institution,
        )
        if start_date is not None:
            query = query.filter(TwInstitutionalSpotDaily.trade_date >= start_date)
        if end_date is not None:
            query = query.filter(TwInstitutionalSpotDaily.trade_date <= end_date)
        return query.order_by(TwInstitutionalSpotDaily.trade_date.asc()).all()
