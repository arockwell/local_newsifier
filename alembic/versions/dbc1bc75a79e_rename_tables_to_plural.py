"""Rename tables to use plural and consistent prefixes.

Revision ID: dbc1bc75a79e
Revises: d6d7f6c7b282
Create Date: 2025-04-26 19:18:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "dbc1bc75a79e"
down_revision: Union[str, None] = "d6d7f6c7b282"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Rename the tables
    op.execute("ALTER TABLE feed_processing_log DROP CONSTRAINT feed_processing_log_feed_id_fkey")
    op.execute(
        "ALTER INDEX ix_feed_processing_log_feed_id RENAME TO ix_rss_feed_processing_logs_feed_id"
    )
    op.execute(
        "ALTER INDEX ix_feed_processing_log_status RENAME TO ix_rss_feed_processing_logs_status"
    )
    op.execute("ALTER INDEX ix_rss_feed_url RENAME TO ix_rss_feeds_url")
    op.execute("ALTER TABLE rss_feed RENAME TO rss_feeds")
    op.execute("ALTER TABLE feed_processing_log RENAME TO rss_feed_processing_logs")

    # Recreate foreign key with new table names
    op.execute(
        "ALTER TABLE rss_feed_processing_logs ADD CONSTRAINT "
        "rss_feed_processing_logs_feed_id_fkey FOREIGN KEY (feed_id) REFERENCES rss_feeds(id)"
    )


def downgrade() -> None:
    """Downgrade database schema."""
    # Rename tables back to original names
    op.execute(
        "ALTER TABLE rss_feed_processing_logs DROP CONSTRAINT rss_feed_processing_logs_feed_id_fkey"
    )
    op.execute(
        "ALTER INDEX ix_rss_feed_processing_logs_feed_id RENAME TO ix_feed_processing_log_feed_id"
    )
    op.execute(
        "ALTER INDEX ix_rss_feed_processing_logs_status RENAME TO ix_feed_processing_log_status"
    )
    op.execute("ALTER INDEX ix_rss_feeds_url RENAME TO ix_rss_feed_url")
    op.execute("ALTER TABLE rss_feeds RENAME TO rss_feed")
    op.execute("ALTER TABLE rss_feed_processing_logs RENAME TO feed_processing_log")

    # Recreate foreign key with original table names
    op.execute(
        "ALTER TABLE feed_processing_log ADD CONSTRAINT "
        "feed_processing_log_feed_id_fkey FOREIGN KEY (feed_id) REFERENCES rss_feed(id)"
    )
