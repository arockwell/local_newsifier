"""Fix apify_webhook_raw table presence.

Revision ID: fix_apify_webhook_raw_table
Revises: 1a51ab641644
Create Date: 2025-05-31 21:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fix_apify_webhook_raw_table"
down_revision: Union[str, None] = "1a51ab641644"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    """Ensure apify_webhook_raw table exists with correct schema."""
    if not table_exists("apify_webhook_raw"):
        # Create the table if it doesn't exist
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
        # Create composite unique constraint on run_id + status
        op.create_unique_constraint(
            "uq_apify_webhook_raw_run_status", "apify_webhook_raw", ["run_id", "status"]
        )
        # Create index on created_at for efficient querying
        op.create_index(
            op.f("ix_apify_webhook_raw_created_at"),
            "apify_webhook_raw",
            ["created_at"],
            unique=False,
        )
        # Create index on run_id for efficient querying
        op.create_index(
            op.f("ix_apify_webhook_raw_run_id"), "apify_webhook_raw", ["run_id"], unique=False
        )
    else:
        # Table exists, ensure it has the correct constraint
        # First, check if old constraint exists and drop it
        bind = op.get_bind()
        inspector = inspect(bind)
        constraints = inspector.get_unique_constraints("apify_webhook_raw")

        # Drop old unique constraint on run_id if it exists
        for constraint in constraints:
            if constraint["column_names"] == ["run_id"]:
                op.drop_constraint(constraint["name"], "apify_webhook_raw", type_="unique")

        # Check if new composite constraint exists
        has_composite = any(c["column_names"] == ["run_id", "status"] for c in constraints)

        if not has_composite:
            # Create composite unique constraint
            op.create_unique_constraint(
                "uq_apify_webhook_raw_run_status", "apify_webhook_raw", ["run_id", "status"]
            )


def downgrade() -> None:
    """Revert to previous state."""
    if table_exists("apify_webhook_raw"):
        # Drop the composite constraint if it exists
        bind = op.get_bind()
        inspector = inspect(bind)
        constraints = inspector.get_unique_constraints("apify_webhook_raw")

        for constraint in constraints:
            if constraint["column_names"] == ["run_id", "status"]:
                op.drop_constraint(constraint["name"], "apify_webhook_raw", type_="unique")

        # Re-create unique constraint on just run_id
        op.create_unique_constraint("apify_webhook_raw_run_id_key", "apify_webhook_raw", ["run_id"])
