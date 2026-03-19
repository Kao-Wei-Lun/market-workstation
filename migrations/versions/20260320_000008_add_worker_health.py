"""add worker health table

Revision ID: 20260320_000008
Revises: 20260320_000007
Create Date: 2026-03-20 00:00:08
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260320_000008"
down_revision = "20260320_000007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "worker_health",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("worker_name", sa.String(length=128), nullable=False),
        sa.Column("worker_role", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_job_name", sa.String(length=64), nullable=True),
        sa.Column("last_job_status", sa.String(length=32), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_worker_health")),
    )
    op.create_index("ix_worker_health_worker_name", "worker_health", ["worker_name"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_worker_health_worker_name", table_name="worker_health")
    op.drop_table("worker_health")
