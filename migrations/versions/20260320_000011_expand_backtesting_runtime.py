"""expand backtesting runtime

Revision ID: 20260320_000011
Revises: 20260320_000010
Create Date: 2026-03-20 00:00:11
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260320_000011"
down_revision = "20260320_000010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("strategies", "instrument_id", existing_type=sa.Integer(), nullable=True)
    op.add_column("backtest_runs", sa.Column("resolved_parameters_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")))
    op.add_column("backtest_runs", sa.Column("metrics_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")))

    op.create_table(
        "backtest_search_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("strategy_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("ranking_metric", sa.String(length=32), nullable=False),
        sa.Column("parameter_space_json", sa.JSON(), nullable=False),
        sa.Column("best_parameters_json", sa.JSON(), nullable=False),
        sa.Column("summary_json", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategies.id"], name=op.f("fk_backtest_search_runs_strategy_id_strategies")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_backtest_search_runs")),
    )

    op.create_table(
        "backtest_search_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("search_run_id", sa.Integer(), nullable=False),
        sa.Column("backtest_run_id", sa.Integer(), nullable=False),
        sa.Column("parameter_set_json", sa.JSON(), nullable=False),
        sa.Column("metrics_json", sa.JSON(), nullable=False),
        sa.Column("ranking_score", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["backtest_run_id"], ["backtest_runs.id"], name=op.f("fk_backtest_search_results_backtest_run_id_backtest_runs")),
        sa.ForeignKeyConstraint(["search_run_id"], ["backtest_search_runs.id"], name=op.f("fk_backtest_search_results_search_run_id_backtest_search_runs")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_backtest_search_results")),
    )

    op.create_table(
        "backtest_walk_forward_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("strategy_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("ranking_metric", sa.String(length=32), nullable=False),
        sa.Column("parameter_space_json", sa.JSON(), nullable=False),
        sa.Column("summary_json", sa.JSON(), nullable=False),
        sa.Column("train_window_days", sa.Integer(), nullable=False),
        sa.Column("test_window_days", sa.Integer(), nullable=False),
        sa.Column("step_days", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategies.id"], name=op.f("fk_backtest_walk_forward_runs_strategy_id_strategies")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_backtest_walk_forward_runs")),
    )

    op.create_table(
        "backtest_walk_forward_windows",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("walk_forward_run_id", sa.Integer(), nullable=False),
        sa.Column("backtest_run_id", sa.Integer(), nullable=False),
        sa.Column("window_index", sa.Integer(), nullable=False),
        sa.Column("train_start_date", sa.Date(), nullable=False),
        sa.Column("train_end_date", sa.Date(), nullable=False),
        sa.Column("test_start_date", sa.Date(), nullable=False),
        sa.Column("test_end_date", sa.Date(), nullable=False),
        sa.Column("selected_parameters_json", sa.JSON(), nullable=False),
        sa.Column("train_metrics_json", sa.JSON(), nullable=False),
        sa.Column("test_metrics_json", sa.JSON(), nullable=False),
        sa.Column("ranking_score", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["backtest_run_id"], ["backtest_runs.id"], name=op.f("fk_backtest_walk_forward_windows_backtest_run_id_backtest_runs")),
        sa.ForeignKeyConstraint(["walk_forward_run_id"], ["backtest_walk_forward_runs.id"], name=op.f("fk_backtest_walk_forward_windows_walk_forward_run_id_backtest_walk_forward_runs")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_backtest_walk_forward_windows")),
    )

    op.alter_column("backtest_runs", "resolved_parameters_json", server_default=None)
    op.alter_column("backtest_runs", "metrics_json", server_default=None)


def downgrade() -> None:
    op.drop_table("backtest_walk_forward_windows")
    op.drop_table("backtest_walk_forward_runs")
    op.drop_table("backtest_search_results")
    op.drop_table("backtest_search_runs")
    op.drop_column("backtest_runs", "metrics_json")
    op.drop_column("backtest_runs", "resolved_parameters_json")
    op.alter_column("strategies", "instrument_id", existing_type=sa.Integer(), nullable=False)
