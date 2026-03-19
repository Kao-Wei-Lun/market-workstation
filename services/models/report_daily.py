from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import Date, DateTime, Index, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from services.db.base import Base


class ReportDaily(Base):
    __tablename__ = "reports_daily"
    __table_args__ = (
        Index(
            "ix_reports_daily_report_date_report_type_report_key",
            "report_date",
            "report_type",
            "report_key",
            unique=True,
        ),
        Index("ix_reports_daily_report_date", "report_date"),
        Index("ix_reports_daily_report_type", "report_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    report_type: Mapped[str] = mapped_column(String(64), nullable=False)
    report_key: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    markdown_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
