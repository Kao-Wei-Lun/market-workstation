"""add tw derivatives tables

Revision ID: 20260319_000003
Revises: 20260319_000002
Create Date: 2026-03-19 00:00:03
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260319_000003"
down_revision = "20260319_000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tw_derivatives_daily",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("market", sa.String(length=32), nullable=False),
        sa.Column("product_code", sa.String(length=32), nullable=False),
        sa.Column("product_name", sa.String(length=128), nullable=True),
        sa.Column("contract_period", sa.String(length=32), nullable=True),
        sa.Column("institution", sa.String(length=64), nullable=False),
        sa.Column("call_put", sa.String(length=16), nullable=True),
        sa.Column("long_open_interest", sa.Integer(), nullable=False),
        sa.Column("short_open_interest", sa.Integer(), nullable=False),
        sa.Column("net_open_interest", sa.Integer(), nullable=False),
        sa.Column("long_amount", sa.Numeric(precision=20, scale=4), nullable=True),
        sa.Column("short_amount", sa.Numeric(precision=20, scale=4), nullable=True),
        sa.Column("net_amount", sa.Numeric(precision=20, scale=4), nullable=True),
        sa.Column("source_route", sa.String(length=64), nullable=False),
        sa.Column("is_options", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tw_derivatives_daily")),
    )
    op.create_index(op.f("ix_tw_derivatives_daily_trade_date"), "tw_derivatives_daily", ["trade_date"], unique=False)
    op.create_index(
        "ix_tw_derivatives_daily_trade_date_market_product_institution",
        "tw_derivatives_daily",
        ["trade_date", "market", "product_code", "institution", "contract_period", "call_put"],
        unique=True,
    )

    op.create_table(
        "tw_derivatives_features",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("daily_record_id", sa.Integer(), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("market", sa.String(length=32), nullable=False),
        sa.Column("product_code", sa.String(length=32), nullable=False),
        sa.Column("contract_period", sa.String(length=32), nullable=True),
        sa.Column("institution", sa.String(length=64), nullable=False),
        sa.Column("call_put", sa.String(length=16), nullable=True),
        sa.Column("delta_1d", sa.Numeric(precision=20, scale=6), nullable=True),
        sa.Column("delta_5d", sa.Numeric(precision=20, scale=6), nullable=True),
        sa.Column("delta_20d", sa.Numeric(precision=20, scale=6), nullable=True),
        sa.Column("zscore_20d", sa.Numeric(precision=20, scale=6), nullable=True),
        sa.Column("regime_label", sa.String(length=32), nullable=False),
        sa.Column("bias_score", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("anomaly_flag", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["daily_record_id"],
            ["tw_derivatives_daily.id"],
            name=op.f("fk_tw_derivatives_features_daily_record_id_tw_derivatives_daily"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tw_derivatives_features")),
        sa.UniqueConstraint("daily_record_id", name=op.f("uq_tw_derivatives_features_daily_record_id")),
    )
    op.create_index(
        op.f("ix_tw_derivatives_features_trade_date"),
        "tw_derivatives_features",
        ["trade_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_tw_derivatives_features_trade_date"), table_name="tw_derivatives_features")
    op.drop_table("tw_derivatives_features")
    op.drop_index(
        "ix_tw_derivatives_daily_trade_date_market_product_institution",
        table_name="tw_derivatives_daily",
    )
    op.drop_index(op.f("ix_tw_derivatives_daily_trade_date"), table_name="tw_derivatives_daily")
    op.drop_table("tw_derivatives_daily")
