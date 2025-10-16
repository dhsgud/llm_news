"""Initial schema with NewsArticle, SentimentAnalysis, and AnalysisCache tables

Revision ID: 001
Revises: 
Create Date: 2025-10-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create news_articles table
    op.create_table(
        'news_articles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('published_date', sa.DateTime(), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('url', sa.String(length=500), nullable=True),
        sa.Column('asset_type', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_news_articles_id'), 'news_articles', ['id'], unique=False)
    op.create_index(op.f('ix_news_articles_published_date'), 'news_articles', ['published_date'], unique=False)
    op.create_index(op.f('ix_news_articles_asset_type'), 'news_articles', ['asset_type'], unique=False)
    op.create_index('idx_published_asset', 'news_articles', ['published_date', 'asset_type'], unique=False)

    # Create sentiment_analysis table
    op.create_table(
        'sentiment_analysis',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('sentiment', sa.String(length=20), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('analyzed_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['article_id'], ['news_articles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sentiment_analysis_id'), 'sentiment_analysis', ['id'], unique=False)
    op.create_index(op.f('ix_sentiment_analysis_article_id'), 'sentiment_analysis', ['article_id'], unique=False)
    op.create_index(op.f('ix_sentiment_analysis_analyzed_at'), 'sentiment_analysis', ['analyzed_at'], unique=False)
    op.create_index('idx_article_analyzed', 'sentiment_analysis', ['article_id', 'analyzed_at'], unique=False)

    # Create analysis_cache table
    op.create_table(
        'analysis_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cache_key', sa.String(length=100), nullable=False),
        sa.Column('result_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analysis_cache_id'), 'analysis_cache', ['id'], unique=False)
    op.create_index(op.f('ix_analysis_cache_cache_key'), 'analysis_cache', ['cache_key'], unique=True)
    op.create_index(op.f('ix_analysis_cache_expires_at'), 'analysis_cache', ['expires_at'], unique=False)
    op.create_index('idx_key_expires', 'analysis_cache', ['cache_key', 'expires_at'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('idx_key_expires', table_name='analysis_cache')
    op.drop_index(op.f('ix_analysis_cache_expires_at'), table_name='analysis_cache')
    op.drop_index(op.f('ix_analysis_cache_cache_key'), table_name='analysis_cache')
    op.drop_index(op.f('ix_analysis_cache_id'), table_name='analysis_cache')
    op.drop_table('analysis_cache')
    
    op.drop_index('idx_article_analyzed', table_name='sentiment_analysis')
    op.drop_index(op.f('ix_sentiment_analysis_analyzed_at'), table_name='sentiment_analysis')
    op.drop_index(op.f('ix_sentiment_analysis_article_id'), table_name='sentiment_analysis')
    op.drop_index(op.f('ix_sentiment_analysis_id'), table_name='sentiment_analysis')
    op.drop_table('sentiment_analysis')
    
    op.drop_index('idx_published_asset', table_name='news_articles')
    op.drop_index(op.f('ix_news_articles_asset_type'), table_name='news_articles')
    op.drop_index(op.f('ix_news_articles_published_date'), table_name='news_articles')
    op.drop_index(op.f('ix_news_articles_id'), table_name='news_articles')
    op.drop_table('news_articles')
