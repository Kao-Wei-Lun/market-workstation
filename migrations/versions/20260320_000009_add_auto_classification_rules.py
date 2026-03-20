"""add auto classification rules

Revision ID: 20260320_000009
Revises: 20260320_000008
Create Date: 2026-03-20 00:00:09
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260320_000009"
down_revision = "20260320_000008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "auto_classification_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("target_tag", sa.String(length=64), nullable=False),
        sa.Column("definition_json", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auto_classification_rules")),
        sa.UniqueConstraint("name", name=op.f("uq_auto_classification_rules_name")),
    )


def downgrade() -> None:
    op.drop_table("auto_classification_rules")
