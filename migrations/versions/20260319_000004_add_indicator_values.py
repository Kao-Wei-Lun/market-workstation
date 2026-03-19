"""add indicator values

Revision ID: 20260319_000004
Revises: 20260319_000003
Create Date: 2026-03-19 00:00:04
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260319_000004"
down_revision = "20260319_000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "indicator_values",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("indicator_name", sa.String(length=64), nullable=False),
        sa.Column("component", sa.String(length=64), nullable=False),
        sa.Column("parameter_signature", sa.String(length=128), nullable=False),
        sa.Column("value", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["instrument_id"],
            ["instruments.id"],
            name=op.f("fk_indicator_values_instrument_id_instruments"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_indicator_values")),
    )
    op.create_index(
        "ix_indicator_values_lookup",
        "indicator_values",
        ["instrument_id", "trade_date", "indicator_name", "component", "parameter_signature"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_indicator_values_lookup",
        table_name="indicator_values",
    )
    op.drop_table("indicator_values")
