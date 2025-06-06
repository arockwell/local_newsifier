"""make article title optional.

Revision ID: e8f921b5c3d1
Revises: dbc1bc75a79e
Create Date: 2025-06-06 01:16:01.000000

"""

import sqlalchemy as sa

from alembic import op

# sqlmodel imported for consistency with other migrations


# revision identifiers, used by Alembic.
revision = "e8f921b5c3d1"
down_revision = "dbc1bc75a79e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Make title column nullable."""
    op.alter_column("articles", "title", existing_type=sa.String(), nullable=True)


def downgrade() -> None:
    """Make title column NOT NULL again.

    Note: This will fail if there are any NULL titles in the database.
    """
    op.alter_column("articles", "title", existing_type=sa.String(), nullable=False)
