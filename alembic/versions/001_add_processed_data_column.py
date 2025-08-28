"""Add processed_data column to audio_calls table

Revision ID: 001
Revises: 
Create Date: 2025-01-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add processed_data column to audio_calls table if it doesn't exist."""
    # Check if the column already exists
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('audio_calls')]
    
    if 'processed_data' not in columns:
        op.add_column('audio_calls', sa.Column('processed_data', postgresql.JSON, nullable=True))
        print("Added processed_data column to audio_calls table")
    else:
        print("processed_data column already exists in audio_calls table")


def downgrade():
    """Remove processed_data column from audio_calls table if it exists."""
    # Check if the column exists before trying to drop it
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('audio_calls')]
    
    if 'processed_data' in columns:
        op.drop_column('audio_calls', 'processed_data')
        print("Removed processed_data column from audio_calls table")
    else:
        print("processed_data column does not exist in audio_calls table")
