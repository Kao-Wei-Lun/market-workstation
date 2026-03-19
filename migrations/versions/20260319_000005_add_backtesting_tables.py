"""add backtesting tables

Revision ID: 20260319_000005
Revises: 20260319_000004
Create Date: 2026-03-19 00:00:05
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260319_000005"
down_revision = "20260319_000004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "strategies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("definition_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.id"], name=op.f("fk_strategies_instrument_id_instruments")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_strategies")),
    )

    op.create_table(
        "backtest_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("strategy_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("initial_cash", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("final_cash", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("total_return", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("total_return_pct", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("total_trades", sa.Integer(), nullable=False),
        sa.Column("win_rate", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("fee_paid", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("tax_paid", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("slippage_paid", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategies.id"], name=op.f("fk_backtest_runs_strategy_id_strategies")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_backtest_runs")),
    )

    op.create_table(
        "backtest_trades",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("entry_date", sa.Date(), nullable=False),
        sa.Column("exit_date", sa.Date(), nullable=False),
        sa.Column("entry_price", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("exit_price", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("gross_pnl", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("net_pnl", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("fee_paid", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("tax_paid", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("slippage_paid", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("holding_period_days", sa.Integer(), nullable=False),
        sa.Column("exit_reason", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.id"], name=op.f("fk_backtest_trades_instrument_id_instruments")),
        sa.ForeignKeyConstraint(["run_id"], ["backtest_runs.id"], name=op.f("fk_backtest_trades_run_id_backtest_runs")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_backtest_trades")),
    )


def downgrade() -> None:
    op.drop_table("backtest_trades")
    op.drop_table("backtest_runs")
    op.drop_table("strategies")
