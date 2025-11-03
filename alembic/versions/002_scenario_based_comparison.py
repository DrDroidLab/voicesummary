"""Add scenario-based comparison fields

Revision ID: 002
Revises: c6352b5edd04
Create Date: 2025-10-19 18:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "002"
down_revision = "c6352b5edd04"
branch_labels = None
depends_on = None


def upgrade():
    """Add scenario-based comparison fields to agent comparison tables."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    # Update agent_comparisons table
    comparisons_columns = [
        col["name"] for col in inspector.get_columns("agent_comparisons")
    ]

    # Remove script_content if it exists, add scenario_config
    if "script_content" in comparisons_columns:
        op.drop_column("agent_comparisons", "script_content")
        print("Dropped script_content column from agent_comparisons table")

    if "scenario_config" not in comparisons_columns:
        op.add_column(
            "agent_comparisons",
            sa.Column("scenario_config", postgresql.JSON, nullable=True),
        )
        print("Added scenario_config column to agent_comparisons table")

    # Update agent_comparison_runs table
    runs_columns = [
        col["name"] for col in inspector.get_columns("agent_comparison_runs")
    ]

    # Add new columns if they don't exist
    if "agent_config" not in runs_columns:
        op.add_column(
            "agent_comparison_runs",
            sa.Column("agent_config", postgresql.JSON, nullable=True),
        )
        print("Added agent_config column to agent_comparison_runs table")

    if "simulated_transcript" not in runs_columns:
        op.add_column(
            "agent_comparison_runs",
            sa.Column("simulated_transcript", postgresql.JSON, nullable=True),
        )
        print("Added simulated_transcript column to agent_comparison_runs table")

    if "total_turns" not in runs_columns:
        op.add_column(
            "agent_comparison_runs", sa.Column("total_turns", sa.Integer, nullable=True)
        )
        print("Added total_turns column to agent_comparison_runs table")

    if "outcome_orientation" not in runs_columns:
        op.add_column(
            "agent_comparison_runs",
            sa.Column("outcome_orientation", sa.Float, nullable=True),
        )
        print("Added outcome_orientation column to agent_comparison_runs table")


def downgrade():
    """Remove scenario-based comparison fields from agent comparison tables."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    # Rollback agent_comparisons table
    comparisons_columns = [
        col["name"] for col in inspector.get_columns("agent_comparisons")
    ]

    if "scenario_config" in comparisons_columns:
        op.drop_column("agent_comparisons", "scenario_config")
        print("Removed scenario_config column from agent_comparisons table")

    if "script_content" not in comparisons_columns:
        op.add_column(
            "agent_comparisons", sa.Column("script_content", sa.Text, nullable=True)
        )
        print("Added back script_content column to agent_comparisons table")

    # Rollback agent_comparison_runs table
    runs_columns = [
        col["name"] for col in inspector.get_columns("agent_comparison_runs")
    ]

    if "agent_config" in runs_columns:
        op.drop_column("agent_comparison_runs", "agent_config")
        print("Removed agent_config column from agent_comparison_runs table")

    if "simulated_transcript" in runs_columns:
        op.drop_column("agent_comparison_runs", "simulated_transcript")
        print("Removed simulated_transcript column from agent_comparison_runs table")

    if "total_turns" in runs_columns:
        op.drop_column("agent_comparison_runs", "total_turns")
        print("Removed total_turns column from agent_comparison_runs table")

    if "outcome_orientation" in runs_columns:
        op.drop_column("agent_comparison_runs", "outcome_orientation")
        print("Removed outcome_orientation column from agent_comparison_runs table")
