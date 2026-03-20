from __future__ import annotations

from datetime import date

from pydantic import BaseModel
from sqlalchemy.orm import Session

from services.core.exports import rows_to_csv
from services.core.reports.generators import generate_market_summary_report
from services.core.reports.base import GeneratedReport
from services.db.repositories.reports import ReportDailyRepository
from services.models.daily_bar import DailyBar
from services.models.report_daily import ReportDaily
from services.schemas.reporting import DailyReportBundleContent, ReportSectionRead


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
    report_date: date | None = None,
    report_type: str | None = None,
    limit: int | None = None,
) -> list[ReportDaily]:
    repository = ReportDailyRepository(session)
    return repository.list_by_date(report_date, report_type=report_type, limit=limit)


def get_latest_report_date(session: Session, *, report_type: str | None = None) -> date | None:
    return ReportDailyRepository(session).get_latest_report_date(report_type=report_type)


def get_report_bundle(session: Session, *, report_date: date) -> DailyReportBundleContent | None:
    report = get_report(session, report_date=report_date, report_type="daily_report_bundle")
    if report is None:
        return None
    return DailyReportBundleContent.model_validate(report.content_json)


def get_report_section(
    session: Session,
    *,
    report_date: date,
    section_type: str,
) -> ReportSectionRead | None:
    bundle = get_report_bundle(session, report_date=report_date)
    if bundle is None:
        return None
    for section in bundle.sections:
        if section.section_type == section_type:
            return section
    return None


def export_report_bundle(
    session: Session,
    *,
    report_date: date,
    export_format: str,
) -> tuple[str, str]:
    bundle = get_report_bundle(session, report_date=report_date)
    if bundle is None:
        msg = "report bundle not found"
        raise ValueError(msg)
    if export_format == "json":
        return f"daily_report_bundle_{report_date.isoformat()}.json", bundle.model_dump_json(indent=2)
    rows = [
        {
            "report_date": report_date.isoformat(),
            "section_type": section.section_type,
            "title": section.title,
            "markdown_body": section.markdown_body,
            "payload_json": section.payload_json,
        }
        for section in bundle.sections
    ]
    return f"daily_report_bundle_{report_date.isoformat()}.csv", rows_to_csv(rows)


def build_latest_market_snapshot(session: Session, *, report_date: date | None = None) -> GeneratedReport | None:
    resolved_date = report_date or session.query(DailyBar.trade_date).order_by(DailyBar.trade_date.desc()).limit(1).scalar()
    if resolved_date is None:
        return None
    return generate_market_summary_report(session, report_date=resolved_date)
