"""add chart annotations

Revision ID: 20260320_000012
Revises: 20260320_000011
Create Date: 2026-03-20 16:30:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260320_000012"
down_revision: str | None = "20260320_000011"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "chart_annotations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("symbol_snapshot", sa.String(length=32), nullable=False),
        sa.Column("view_kind", sa.String(length=32), nullable=False),
        sa.Column("annotation_type", sa.String(length=32), nullable=False),
        sa.Column("timeframe", sa.String(length=16), nullable=False),
        sa.Column("label", sa.String(length=128), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_chart_annotations_instrument_view_kind",
        "chart_annotations",
        ["instrument_id", "view_kind"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_chart_annotations_instrument_view_kind", table_name="chart_annotations")
    op.drop_table("chart_annotations")
