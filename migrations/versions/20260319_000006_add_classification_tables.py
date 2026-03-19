"""add classification tables

Revision ID: 20260319_000006
Revises: 20260319_000005
Create Date: 2026-03-19 00:00:06
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260319_000006"
down_revision = "20260319_000005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "instrument_tags",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("tag", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["instrument_id"],
            ["instruments.id"],
            name=op.f("fk_instrument_tags_instrument_id_instruments"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_instrument_tags")),
    )
    op.create_index(
        "ix_instrument_tags_instrument_id_tag",
        "instrument_tags",
        ["instrument_id", "tag"],
        unique=True,
    )

    op.create_table(
        "watchlists",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_watchlists")),
        sa.UniqueConstraint("name", name=op.f("uq_watchlists_name")),
    )

    op.create_table(
        "watchlist_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("watchlist_id", sa.Integer(), nullable=False),
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["instrument_id"],
            ["instruments.id"],
            name=op.f("fk_watchlist_items_instrument_id_instruments"),
        ),
        sa.ForeignKeyConstraint(
            ["watchlist_id"],
            ["watchlists.id"],
            name=op.f("fk_watchlist_items_watchlist_id_watchlists"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_watchlist_items")),
    )
    op.create_index(
        "ix_watchlist_items_watchlist_id_instrument_id",
        "watchlist_items",
        ["watchlist_id", "instrument_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_watchlist_items_watchlist_id_instrument_id", table_name="watchlist_items")
    op.drop_table("watchlist_items")
    op.drop_table("watchlists")
    op.drop_index("ix_instrument_tags_instrument_id_tag", table_name="instrument_tags")
    op.drop_table("instrument_tags")
