"""fix apify webhook unique constraint.

Revision ID: 1a51ab641644
Revises: a8c61d1f7283
Create Date: 2025-05-31 18:28:14.264379

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1a51ab641644"
down_revision: Union[str, None] = "a8c61d1f7283"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop the existing unique constraint on run_id if it exists
    # Using a try/except to handle the case where the constraint doesn't exist
    from sqlalchemy import text

    connection = op.get_bind()

    # Check if constraint exists before trying to drop it
    result = connection.execute(
        text(
            """
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name = 'apify_webhook_raw'
        AND constraint_name = 'apify_webhook_raw_run_id_key'
        AND constraint_type = 'UNIQUE'
    """
        )
    )

    if result.fetchone():
        op.drop_constraint("apify_webhook_raw_run_id_key", "apify_webhook_raw", type_="unique")

    # Create a composite unique constraint on run_id + status
    op.create_unique_constraint(
        "uq_apify_webhook_raw_run_status", "apify_webhook_raw", ["run_id", "status"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the composite unique constraint
    op.drop_constraint("uq_apify_webhook_raw_run_status", "apify_webhook_raw", type_="unique")

    # Restore the original unique constraint on run_id
    op.create_unique_constraint("apify_webhook_raw_run_id_key", "apify_webhook_raw", ["run_id"])
