"""Add schedule_id to apify_source_configs

Revision ID: add_schedule_id_to_apify_config
Revises: d6d7f6c7b282
Create Date: 2023-05-08 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'add_schedule_id_to_apify_config'
down_revision: Union[str, None] = 'd6d7f6c7b282'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the schedule_id column to the apify_source_configs table
    op.add_column('apify_source_configs', sa.Column('schedule_id', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove the schedule_id column from the apify_source_configs table
    op.drop_column('apify_source_configs', 'schedule_id')