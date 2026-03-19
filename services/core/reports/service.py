from __future__ import annotations

from datetime import date

from pydantic import BaseModel
from sqlalchemy.orm import Session

from services.core.reports.base import GeneratedReport
from services.db.repositories.reports import ReportDailyRepository
from services.models.report_daily import ReportDaily


def persist_generated_report(session: Session, report: GeneratedReport[BaseModel]) -> ReportDaily:
    repository = ReportDailyRepository(session)
    persisted = repository.upsert(
        report_date=report.report_date,
        report_type=report.report_type,
        report_key=report.report_key,
        title=report.title,
        content_json=report.content_json(),
        markdown_text=report.markdown_text,
    )
    session.commit()
    session.refresh(persisted)
    return persisted


def get_report(
    session: Session,
    *,
    report_date: date,
    report_type: str,
    report_key: str = "",
) -> ReportDaily | None:
    repository = ReportDailyRepository(session)
    return repository.get_by_identity(
        report_date=report_date,
        report_type=report_type,
        report_key=report_key,
    )


def list_reports(
    session: Session,
    *,
    report_date: date,
    report_type: str | None = None,
) -> list[ReportDaily]:
    repository = ReportDailyRepository(session)
    return repository.list_by_date(report_date, report_type=report_type)
