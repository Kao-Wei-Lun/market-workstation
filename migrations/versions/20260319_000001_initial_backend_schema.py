"""initial backend schema

Revision ID: 20260319_000001
Revises:
Create Date: 2026-03-19 00:00:01
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260319_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ingest_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_route", sa.String(length=64), nullable=False),
        sa.Column("job_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ingest_jobs")),
    )
    op.create_index(op.f("ix_ingest_jobs_status"), "ingest_jobs", ["status"], unique=False)
    op.create_index(
        "ix_ingest_jobs_source_route_trade_date",
        "ingest_jobs",
        ["source_route", "trade_date"],
        unique=False,
    )

    op.create_table(
        "instruments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("market", sa.String(length=32), nullable=False),
        sa.Column("asset_type", sa.String(length=32), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("source_route", sa.String(length=64), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_instruments")),
        sa.UniqueConstraint("symbol", name=op.f("uq_instruments_symbol")),
    )
    op.create_index(op.f("ix_instruments_asset_type"), "instruments", ["asset_type"], unique=False)
    op.create_index(op.f("ix_instruments_market"), "instruments", ["market"], unique=False)
    op.create_index(op.f("ix_instruments_symbol"), "instruments", ["symbol"], unique=True)

    op.create_table(
        "daily_bars",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("open", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("high", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("low", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("close", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("volume", sa.Integer(), nullable=False),
        sa.Column("turnover_value", sa.Numeric(precision=20, scale=4), nullable=True),
        sa.Column("transactions_count", sa.Integer(), nullable=True),
        sa.Column("change", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("change_percent", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["instrument_id"],
            ["instruments.id"],
            name=op.f("fk_daily_bars_instrument_id_instruments"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_daily_bars")),
    )
    op.create_index(
        "ix_daily_bars_instrument_id_trade_date",
        "daily_bars",
        ["instrument_id", "trade_date"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_daily_bars_instrument_id_trade_date", table_name="daily_bars")
    op.drop_table("daily_bars")
    op.drop_index(op.f("ix_instruments_symbol"), table_name="instruments")
    op.drop_index(op.f("ix_instruments_market"), table_name="instruments")
    op.drop_index(op.f("ix_instruments_asset_type"), table_name="instruments")
    op.drop_table("instruments")
    op.drop_index("ix_ingest_jobs_source_route_trade_date", table_name="ingest_jobs")
    op.drop_index(op.f("ix_ingest_jobs_status"), table_name="ingest_jobs")
    op.drop_table("ingest_jobs")
