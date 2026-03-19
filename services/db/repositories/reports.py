from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from services.models.report_daily import ReportDaily


class ReportDailyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert(
        self,
        *,
        report_date: date,
        report_type: str,
        report_key: str,
        title: str,
        content_json: dict[str, Any],
        markdown_text: str,
    ) -> ReportDaily:
        report = self.get_by_identity(
            report_date=report_date,
            report_type=report_type,
            report_key=report_key,
        )
        if report is None:
            report = ReportDaily(
                report_date=report_date,
                report_type=report_type,
                report_key=report_key,
                title=title,
                content_json=content_json,
                markdown_text=markdown_text,
            )
            self.session.add(report)
        else:
            report.title = title
            report.content_json = content_json
            report.markdown_text = markdown_text

        self.session.flush()
        return report

    def get_by_identity(
        self,
        *,
        report_date: date,
        report_type: str,
        report_key: str = "",
    ) -> ReportDaily | None:
        return (
            self.session.query(ReportDaily)
            .filter(
                ReportDaily.report_date == report_date,
                ReportDaily.report_type == report_type,
                ReportDaily.report_key == report_key,
            )
            .one_or_none()
        )

    def list_by_date(
        self,
        report_date: date,
        *,
        report_type: str | None = None,
    ) -> list[ReportDaily]:
        query = self.session.query(ReportDaily).filter(ReportDaily.report_date == report_date)
        if report_type is not None:
            query = query.filter(ReportDaily.report_type == report_type)
        return query.order_by(ReportDaily.report_type.asc(), ReportDaily.report_key.asc()).all()
