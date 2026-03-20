"""add tw institutional spot daily

Revision ID: 20260320_000013
Revises: 20260320_000012
Create Date: 2026-03-20 21:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260320_000013"
down_revision: str | None = "20260320_000012"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tw_institutional_spot_daily",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("market", sa.String(length=32), nullable=False),
        sa.Column("institution", sa.String(length=64), nullable=False),
        sa.Column("buy_amount", sa.Numeric(20, 4), nullable=False),
        sa.Column("sell_amount", sa.Numeric(20, 4), nullable=False),
        sa.Column("net_amount", sa.Numeric(20, 4), nullable=False),
        sa.Column("source_route", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_tw_institutional_spot_daily_trade_date_market_institution",
        "tw_institutional_spot_daily",
        ["trade_date", "market", "institution"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_tw_institutional_spot_daily_trade_date_market_institution", table_name="tw_institutional_spot_daily")
    op.drop_table("tw_institutional_spot_daily")
