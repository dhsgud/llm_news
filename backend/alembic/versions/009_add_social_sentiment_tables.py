"""add social sentiment tables

Revision ID: 009
Revises: 008
Create Date: 2025-10-16

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create social_posts table
    op.create_table(
        'social_posts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.String(20), nullable=False),
        sa.Column('post_id', sa.String(100), nullable=False),
        sa.Column('symbol', sa.String(20), nullable=True),
        sa.Column('author', sa.String(100), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('url', sa.String(500), nullable=True),
        sa.Column('likes', sa.Integer(), default=0),
        sa.Column('shares', sa.Integer(), default=0),
        sa.Column('comments', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('collected_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_social_posts_id', 'social_posts', ['id'])
    op.create_index('idx_social_posts_post_id', 'social_posts', ['post_id'], unique=True)
    op.create_index('idx_social_posts_symbol', 'social_posts', ['symbol'])
    op.create_index('idx_social_symbol_created', 'social_posts', ['symbol', 'created_at'])
    op.create_index('idx_social_platform_created', 'social_posts', ['platform', 'created_at'])

    # Create social_sentiments table
    op.create_table(
        'social_sentiments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('sentiment', sa.String(20), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('analyzed_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['post_id'], ['social_posts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_social_sentiments_id', 'social_sentiments', ['id'])
    op.create_index('idx_social_sentiments_post_id', 'social_sentiments', ['post_id'])
    op.create_index('idx_social_sentiment_post', 'social_sentiments', ['post_id', 'analyzed_at'])

    # Create aggregated_social_sentiments table
    op.create_table(
        'aggregated_social_sentiments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(20), nullable=True),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('platform', sa.String(20), nullable=False),
        sa.Column('post_count', sa.Integer(), default=0),
        sa.Column('avg_sentiment_score', sa.Float(), default=0.0),
        sa.Column('positive_count', sa.Integer(), default=0),
        sa.Column('negative_count', sa.Integer(), default=0),
        sa.Column('neutral_count', sa.Integer(), default=0),
        sa.Column('total_engagement', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_aggregated_social_sentiments_id', 'aggregated_social_sentiments', ['id'])
    op.create_index('idx_aggregated_social_sentiments_symbol', 'aggregated_social_sentiments', ['symbol'])
    op.create_index('idx_aggregated_social_sentiments_date', 'aggregated_social_sentiments', ['date'])
    op.create_index('idx_agg_social_symbol_date', 'aggregated_social_sentiments', ['symbol', 'date'])


def downgrade() -> None:
    op.drop_table('aggregated_social_sentiments')
    op.drop_table('social_sentiments')
    op.drop_table('social_posts')
