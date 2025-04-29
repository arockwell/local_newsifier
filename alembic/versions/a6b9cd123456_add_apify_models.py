"""Add Apify models

Revision ID: a6b9cd123456
Revises: rename_tables_to_plural
Create Date: 2025-04-29 04:23:30.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a6b9cd123456'
down_revision: Union[str, None] = 'rename_tables_to_plural'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create apify_source_configs table
    op.create_table('apify_source_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('actor_id', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('schedule', sa.String(), nullable=True),
        sa.Column('source_type', sa.String(), nullable=False),
        sa.Column('source_url', sa.String(), nullable=True),
        sa.Column('input_configuration', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_apify_source_configs_name'), 'apify_source_configs', ['name'], unique=False)
    
    # Create apify_jobs table
    op.create_table('apify_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_config_id', sa.Integer(), nullable=True),
        sa.Column('run_id', sa.String(), nullable=False),
        sa.Column('actor_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('dataset_id', sa.String(), nullable=True),
        sa.Column('item_count', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('processed', sa.Boolean(), nullable=False, default=False),
        sa.Column('articles_created', sa.Integer(), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['source_config_id'], ['apify_source_configs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_apify_jobs_source_config_id'), 'apify_jobs', ['source_config_id'], unique=False)
    op.create_index(op.f('ix_apify_jobs_run_id'), 'apify_jobs', ['run_id'], unique=False)
    
    # Create apify_dataset_items table
    op.create_table('apify_dataset_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('apify_id', sa.String(), nullable=False),
        sa.Column('raw_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('transformed', sa.Boolean(), nullable=False, default=False),
        sa.Column('article_id', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ),
        sa.ForeignKeyConstraint(['job_id'], ['apify_jobs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_apify_dataset_items_job_id'), 'apify_dataset_items', ['job_id'], unique=False)
    op.create_index(op.f('ix_apify_dataset_items_article_id'), 'apify_dataset_items', ['article_id'], unique=False)
    
    # Create apify_credentials table
    op.create_table('apify_credentials',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('api_token', sa.String(), nullable=False),
        sa.Column('label', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('rate_limit_remaining', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_apify_credentials_label'), 'apify_credentials', ['label'], unique=False)
    
    # Create apify_webhooks table
    op.create_table('apify_webhooks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('webhook_id', sa.String(), nullable=False),
        sa.Column('actor_id', sa.String(), nullable=True),
        sa.Column('event_types', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('payload_template', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_apify_webhooks_webhook_id'), 'apify_webhooks', ['webhook_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables in reverse order of creation to avoid foreign key constraints
    op.drop_index(op.f('ix_apify_webhooks_webhook_id'), table_name='apify_webhooks')
    op.drop_table('apify_webhooks')
    
    op.drop_index(op.f('ix_apify_credentials_label'), table_name='apify_credentials')
    op.drop_table('apify_credentials')
    
    op.drop_index(op.f('ix_apify_dataset_items_article_id'), table_name='apify_dataset_items')
    op.drop_index(op.f('ix_apify_dataset_items_job_id'), table_name='apify_dataset_items')
    op.drop_table('apify_dataset_items')
    
    op.drop_index(op.f('ix_apify_jobs_run_id'), table_name='apify_jobs')
    op.drop_index(op.f('ix_apify_jobs_source_config_id'), table_name='apify_jobs')
    op.drop_table('apify_jobs')
    
    op.drop_index(op.f('ix_apify_source_configs_name'), table_name='apify_source_configs')
    op.drop_table('apify_source_configs')
