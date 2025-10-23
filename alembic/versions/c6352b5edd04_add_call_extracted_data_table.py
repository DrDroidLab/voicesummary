"""add_call_extracted_data_table

Revision ID: c6352b5edd04
Revises: 001
Create Date: 2025-09-02 17:12:57.651858

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "c6352b5edd04"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create call_extracted_data table
    op.create_table(
        "call_extracted_data",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("call_id", sa.String(length=255), nullable=False),
        sa.Column("extraction_data", sa.JSON(), nullable=True),
        sa.Column("classification_data", sa.JSON(), nullable=True),
        sa.Column("labeling_data", sa.JSON(), nullable=True),
        sa.Column("processing_status", sa.String(length=50), nullable=True),
        sa.Column("processing_errors", sa.JSON(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["call_id"],
            ["audio_calls.call_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create index on call_id for better query performance
    op.create_index(
        op.f("ix_call_extracted_data_call_id"),
        "call_extracted_data",
        ["call_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_call_extracted_data_id"), "call_extracted_data", ["id"], unique=False
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f("ix_call_extracted_data_id"), table_name="call_extracted_data")
    op.drop_index(
        op.f("ix_call_extracted_data_call_id"), table_name="call_extracted_data"
    )

    # Drop table
    op.drop_table("call_extracted_data")
