"""Add RSS feed models.

Revision ID: d6d7f6c7b282
Revises: d3d111e9579d
Create Date: 2025-04-26 17:20:09.373755

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d6d7f6c7b282"
down_revision: Union[str, None] = "d3d111e9579d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create the RSS feed tables
    op.create_table(
        "rss_feed",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_fetched_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_rss_feed_url"), "rss_feed", ["url"], unique=True)

    op.create_table(
        "feed_processing_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("feed_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("articles_found", sa.Integer(), nullable=False),
        sa.Column("articles_added", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["feed_id"],
            ["rss_feed.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_feed_processing_log_feed_id"),
        "feed_processing_log",
        ["feed_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_feed_processing_log_status"),
        "feed_processing_log",
        ["status"],
        unique=False,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # Simply drop the tables we created
    op.drop_index(op.f("ix_feed_processing_log_status"), table_name="feed_processing_log")
    op.drop_index(op.f("ix_feed_processing_log_feed_id"), table_name="feed_processing_log")
    op.drop_table("feed_processing_log")
    op.drop_index(op.f("ix_rss_feed_url"), table_name="rss_feed")
    op.drop_table("rss_feed")
    # ### end Alembic commands ###
