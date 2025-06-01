"""Add apify_webhook_raw table.

Revision ID: a8c61d1f7283
Revises: add_schedule_id_to_apify_config
Create Date: 2025-05-25 20:55:37.180050

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a8c61d1f7283"
down_revision: Union[str, None] = "13e391b8dbdc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create apify_webhook_raw table
    op.create_table(
        "apify_webhook_raw",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("actor_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    # Create unique index on run_id
    op.create_index(
        op.f("ix_apify_webhook_raw_run_id"), "apify_webhook_raw", ["run_id"], unique=True
    )
    # Create index on created_at for efficient querying
    op.create_index(
        op.f("ix_apify_webhook_raw_created_at"), "apify_webhook_raw", ["created_at"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index(op.f("ix_apify_webhook_raw_created_at"), table_name="apify_webhook_raw")
    op.drop_index(op.f("ix_apify_webhook_raw_run_id"), table_name="apify_webhook_raw")
    # Drop table
    op.drop_table("apify_webhook_raw")
