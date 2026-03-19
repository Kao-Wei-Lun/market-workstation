"""add series points

Revision ID: 20260319_000002
Revises: 20260319_000001
Create Date: 2026-03-19 00:00:02
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260319_000002"
down_revision = "20260319_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "series_points",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("instrument_id", sa.Integer(), nullable=True),
        sa.Column("series_key", sa.String(length=128), nullable=False),
        sa.Column("source_route", sa.String(length=64), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("value", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["instrument_id"],
            ["instruments.id"],
            name=op.f("fk_series_points_instrument_id_instruments"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_series_points")),
    )
    op.create_index(
        "ix_series_points_series_key_trade_date",
        "series_points",
        ["series_key", "trade_date"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_series_points_series_key_trade_date", table_name="series_points")
    op.drop_table("series_points")
