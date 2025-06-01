"""Add schedule_id to apify_source_configs.

Revision ID: 13e391b8dbdc
Revises: a6b9cd123456
Create Date: 2023-05-08 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "13e391b8dbdc"
down_revision: Union[str, None] = "a6b9cd123456"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add the schedule_id column to the apify_source_configs table."""
    op.add_column("apify_source_configs", sa.Column("schedule_id", sa.String(), nullable=True))


def downgrade() -> None:
    """Remove the schedule_id column from the apify_source_configs table."""
    op.drop_column("apify_source_configs", "schedule_id")
