"""multi_simulation_support

Revision ID: 003_multi_simulation_support
Revises: 002_scenario_based_comparison
Create Date: 2025-10-20

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add num_simulations to agent_comparisons table
    op.add_column(
        "agent_comparisons",
        sa.Column("num_simulations", sa.Integer(), nullable=False, server_default="10"),
    )

    # Add simulation_number to agent_comparison_runs table
    op.add_column(
        "agent_comparison_runs",
        sa.Column("simulation_number", sa.Integer(), nullable=True),
    )

    # Create agent_comparison_aggregates table
    op.create_table(
        "agent_comparison_aggregates",
        sa.Column("aggregate_id", sa.String(length=255), nullable=False),
        sa.Column("comparison_id", sa.String(length=255), nullable=False),
        sa.Column("agent_id", sa.String(length=255), nullable=False),
        sa.Column("agent_name", sa.String(length=255), nullable=True),
        # Simulation counts
        sa.Column("total_simulations", sa.Integer(), nullable=False),
        sa.Column("successful_simulations", sa.Integer(), nullable=False),
        sa.Column("failed_simulations", sa.Integer(), nullable=False),
        # Latency stats (mean and std for each percentile)
        sa.Column("latency_median_mean", sa.Float(), nullable=True),
        sa.Column("latency_median_std", sa.Float(), nullable=True),
        sa.Column("latency_p75_mean", sa.Float(), nullable=True),
        sa.Column("latency_p75_std", sa.Float(), nullable=True),
        sa.Column("latency_p99_mean", sa.Float(), nullable=True),
        sa.Column("latency_p99_std", sa.Float(), nullable=True),
        # Accuracy stats
        sa.Column("accuracy_mean", sa.Float(), nullable=True),
        sa.Column("accuracy_std", sa.Float(), nullable=True),
        sa.Column("accuracy_min", sa.Float(), nullable=True),
        sa.Column("accuracy_max", sa.Float(), nullable=True),
        # Humanlike stats
        sa.Column("humanlike_mean", sa.Float(), nullable=True),
        sa.Column("humanlike_std", sa.Float(), nullable=True),
        sa.Column("humanlike_min", sa.Float(), nullable=True),
        sa.Column("humanlike_max", sa.Float(), nullable=True),
        # Outcome orientation stats
        sa.Column("outcome_mean", sa.Float(), nullable=True),
        sa.Column("outcome_std", sa.Float(), nullable=True),
        sa.Column("outcome_min", sa.Float(), nullable=True),
        sa.Column("outcome_max", sa.Float(), nullable=True),
        # Composite score stats
        sa.Column("composite_score_mean", sa.Float(), nullable=True),
        sa.Column("composite_score_std", sa.Float(), nullable=True),
        # Turn stats
        sa.Column("avg_turns_mean", sa.Float(), nullable=True),
        sa.Column("avg_turns_std", sa.Float(), nullable=True),
        # Hangup success rate
        sa.Column("hangup_success_rate", sa.Float(), nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("aggregate_id"),
        sa.ForeignKeyConstraint(
            ["comparison_id"], ["agent_comparisons.comparison_id"], ondelete="CASCADE"
        ),
    )

    # Create indexes
    op.create_index(
        "ix_agent_comparison_aggregates_aggregate_id",
        "agent_comparison_aggregates",
        ["aggregate_id"],
    )
    op.create_index(
        "ix_agent_comparison_aggregates_comparison_id",
        "agent_comparison_aggregates",
        ["comparison_id"],
    )
    op.create_index(
        "ix_agent_comparison_aggregates_agent_id",
        "agent_comparison_aggregates",
        ["agent_id"],
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index(
        "ix_agent_comparison_aggregates_agent_id",
        table_name="agent_comparison_aggregates",
    )
    op.drop_index(
        "ix_agent_comparison_aggregates_comparison_id",
        table_name="agent_comparison_aggregates",
    )
    op.drop_index(
        "ix_agent_comparison_aggregates_aggregate_id",
        table_name="agent_comparison_aggregates",
    )

    # Drop agent_comparison_aggregates table
    op.drop_table("agent_comparison_aggregates")

    # Remove simulation_number from agent_comparison_runs
    op.drop_column("agent_comparison_runs", "simulation_number")

    # Remove num_simulations from agent_comparisons
    op.drop_column("agent_comparisons", "num_simulations")
