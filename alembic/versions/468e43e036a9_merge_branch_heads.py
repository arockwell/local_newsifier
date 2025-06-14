"""Merge branch heads.

Revision ID: 468e43e036a9
Revises: 1a51ab641644, e8f921b5c3d1
Create Date: 2025-06-13 20:09:45.026941

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "468e43e036a9"
down_revision: Union[str, None] = ("1a51ab641644", "e8f921b5c3d1")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
