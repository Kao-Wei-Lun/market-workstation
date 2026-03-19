"""add reports daily table

Revision ID: 20260320_000007
Revises: 20260319_000006
Create Date: 2026-03-20 00:00:07
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260320_000007"
down_revision = "20260319_000006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reports_daily",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("report_type", sa.String(length=64), nullable=False),
        sa.Column("report_key", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content_json", sa.JSON(), nullable=False),
        sa.Column("markdown_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reports_daily")),
    )
    op.create_index(op.f("ix_reports_daily_report_date"), "reports_daily", ["report_date"], unique=False)
    op.create_index(op.f("ix_reports_daily_report_type"), "reports_daily", ["report_type"], unique=False)
    op.create_index(
        "ix_reports_daily_report_date_report_type_report_key",
        "reports_daily",
        ["report_date", "report_type", "report_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_reports_daily_report_date_report_type_report_key", table_name="reports_daily")
    op.drop_index(op.f("ix_reports_daily_report_type"), table_name="reports_daily")
    op.drop_index(op.f("ix_reports_daily_report_date"), table_name="reports_daily")
    op.drop_table("reports_daily")
