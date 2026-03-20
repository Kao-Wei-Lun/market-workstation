"""add candidate tables

Revision ID: 20260320_000010
Revises: 20260320_000009
Create Date: 2026-03-20 00:00:10
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260320_000010"
down_revision = "20260320_000009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "candidate_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("candidate_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("total_candidates", sa.Integer(), nullable=False),
        sa.Column("generation_config_json", sa.JSON(), nullable=False),
        sa.Column("summary_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_candidate_runs")),
    )
    op.create_index("ix_candidate_runs_candidate_date", "candidate_runs", ["candidate_date"], unique=False)

    op.create_table(
        "candidate_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("candidate_date", sa.Date(), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("score", sa.Numeric(20, 6), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("candidate_reasons_json", sa.JSON(), nullable=False),
        sa.Column("supporting_metrics_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.id"], name=op.f("fk_candidate_items_instrument_id_instruments")),
        sa.ForeignKeyConstraint(["run_id"], ["candidate_runs.id"], name=op.f("fk_candidate_items_run_id_candidate_runs")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_candidate_items")),
    )
    op.create_index("ix_candidate_items_candidate_date", "candidate_items", ["candidate_date"], unique=False)
    op.create_index("ix_candidate_items_run_id_instrument_id", "candidate_items", ["run_id", "instrument_id"], unique=True)
    op.create_index("ix_candidate_items_run_id_rank", "candidate_items", ["run_id", "rank"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_candidate_items_run_id_rank", table_name="candidate_items")
    op.drop_index("ix_candidate_items_run_id_instrument_id", table_name="candidate_items")
    op.drop_index("ix_candidate_items_candidate_date", table_name="candidate_items")
    op.drop_table("candidate_items")
    op.drop_index("ix_candidate_runs_candidate_date", table_name="candidate_runs")
    op.drop_table("candidate_runs")
