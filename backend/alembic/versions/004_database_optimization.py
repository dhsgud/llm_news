"""Database optimization: Add indexes, improve query performance

Revision ID: 004
Revises: 003
Create Date: 2025-10-11 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add optimized indexes for common query patterns
    Note: Some indexes may already exist from model definitions
    """
    from sqlalchemy import inspect
    from alembic import op
    
    # Get connection and inspector
    conn = op.get_bind()
    inspector = inspect(conn)
    
    def index_exists(table_name: str, index_name: str) -> bool:
        """Check if an index already exists"""
        indexes = inspector.get_indexes(table_name)
        return any(idx['name'] == index_name for idx in indexes)
    
    # ===== NEWS_ARTICLES OPTIMIZATIONS =====
    # Composite index for date range queries with filtering
    if not index_exists('news_articles', 'idx_news_created_published'):
        op.create_index(
            'idx_news_created_published',
            'news_articles',
            ['created_at', 'published_date'],
            unique=False
        )
    
    # Index for source-based queries
    if not index_exists('news_articles', 'idx_news_source'):
        op.create_index(
            'idx_news_source',
            'news_articles',
            ['source'],
            unique=False
        )
    
    # ===== SENTIMENT_ANALYSIS OPTIMIZATIONS =====
    # Composite index for sentiment filtering with date range
    if not index_exists('sentiment_analysis', 'idx_sentiment_score_date'):
        op.create_index(
            'idx_sentiment_score_date',
            'sentiment_analysis',
            ['sentiment', 'analyzed_at'],
            unique=False
        )
    
    # Index for score-based queries (finding extreme sentiments)
    if not index_exists('sentiment_analysis', 'idx_sentiment_score'):
        op.create_index(
            'idx_sentiment_score',
            'sentiment_analysis',
            ['score'],
            unique=False
        )
    
    # ===== STOCK_PRICES OPTIMIZATIONS =====
    # Composite index for price range queries
    if not index_exists('stock_prices', 'idx_stock_price_range'):
        op.create_index(
            'idx_stock_price_range',
            'stock_prices',
            ['symbol', 'timestamp', 'price'],
            unique=False
        )
    
    # Index for volume-based queries (high volume detection)
    if not index_exists('stock_prices', 'idx_stock_volume'):
        op.create_index(
            'idx_stock_volume',
            'stock_prices',
            ['volume'],
            unique=False
        )
    
    # ===== TRADE_HISTORY OPTIMIZATIONS =====
    # Composite index for symbol-based performance analysis
    if not index_exists('trade_history', 'idx_trade_symbol_status'):
        op.create_index(
            'idx_trade_symbol_status',
            'trade_history',
            ['symbol', 'status', 'executed_at'],
            unique=False
        )
    
    # Index for signal ratio analysis
    if not index_exists('trade_history', 'idx_trade_signal_ratio'):
        op.create_index(
            'idx_trade_signal_ratio',
            'trade_history',
            ['signal_ratio'],
            unique=False
        )
    
    # ===== STOCK_NEWS_RELATION OPTIMIZATIONS =====
    # Index for relevance-based filtering
    if not index_exists('stock_news_relation', 'idx_stock_news_relevance'):
        op.create_index(
            'idx_stock_news_relevance',
            'stock_news_relation',
            ['relevance_score'],
            unique=False
        )
    
    # ===== ACCOUNT_HOLDINGS OPTIMIZATIONS =====
    # Index for updated_at queries (finding stale data)
    if not index_exists('account_holdings', 'idx_holdings_updated'):
        op.create_index(
            'idx_holdings_updated',
            'account_holdings',
            ['updated_at'],
            unique=False
        )
    
    # ===== AUTO_TRADE_CONFIG OPTIMIZATIONS =====
    # Index for active config queries
    if not index_exists('auto_trade_config', 'idx_config_enabled'):
        op.create_index(
            'idx_config_enabled',
            'auto_trade_config',
            ['is_enabled'],
            unique=False
        )
    
    # ===== ANALYSIS_CACHE OPTIMIZATIONS =====
    # Already has good indexes from migration 001
    # No additional indexes needed


def downgrade() -> None:
    """
    Remove optimization indexes
    """
    
    # Drop indexes in reverse order
    op.drop_index('idx_config_enabled', table_name='auto_trade_config')
    op.drop_index('idx_holdings_updated', table_name='account_holdings')
    op.drop_index('idx_stock_news_relevance', table_name='stock_news_relation')
    op.drop_index('idx_trade_signal_ratio', table_name='trade_history')
    op.drop_index('idx_trade_symbol_status', table_name='trade_history')
    op.drop_index('idx_stock_volume', table_name='stock_prices')
    op.drop_index('idx_stock_price_range', table_name='stock_prices')
    op.drop_index('idx_sentiment_score', table_name='sentiment_analysis')
    op.drop_index('idx_sentiment_score_date', table_name='sentiment_analysis')
    op.drop_index('idx_news_source', table_name='news_articles')
    op.drop_index('idx_news_created_published', table_name='news_articles')
