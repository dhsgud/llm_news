"""Add stock data tables: StockPrice, StockNewsRelation, AccountHolding

Revision ID: 002
Revises: 001
Create Date: 2025-10-07 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create stock_prices table
    op.create_table(
        'stock_prices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('price', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('volume', sa.BigInteger(), nullable=True),
        sa.Column('open_price', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('high_price', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('low_price', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stock_prices_id'), 'stock_prices', ['id'], unique=False)
    op.create_index(op.f('ix_stock_prices_symbol'), 'stock_prices', ['symbol'], unique=False)
    op.create_index(op.f('ix_stock_prices_timestamp'), 'stock_prices', ['timestamp'], unique=False)
    op.create_index('idx_symbol_timestamp', 'stock_prices', ['symbol', 'timestamp'], unique=False)

    # Create stock_news_relation table
    op.create_table(
        'stock_news_relation',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stock_symbol', sa.String(length=20), nullable=False),
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('relevance_score', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['article_id'], ['news_articles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stock_news_relation_id'), 'stock_news_relation', ['id'], unique=False)
    op.create_index(op.f('ix_stock_news_relation_stock_symbol'), 'stock_news_relation', ['stock_symbol'], unique=False)
    op.create_index(op.f('ix_stock_news_relation_article_id'), 'stock_news_relation', ['article_id'], unique=False)
    op.create_index('idx_stock_article', 'stock_news_relation', ['stock_symbol', 'article_id'], unique=False)

    # Create account_holdings table
    op.create_table(
        'account_holdings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('average_price', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('current_price', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_account_holdings_id'), 'account_holdings', ['id'], unique=False)
    op.create_index(op.f('ix_account_holdings_symbol'), 'account_holdings', ['symbol'], unique=False)
    op.create_index('idx_holding_symbol', 'account_holdings', ['symbol'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('idx_holding_symbol', table_name='account_holdings')
    op.drop_index(op.f('ix_account_holdings_symbol'), table_name='account_holdings')
    op.drop_index(op.f('ix_account_holdings_id'), table_name='account_holdings')
    op.drop_table('account_holdings')
    
    op.drop_index('idx_stock_article', table_name='stock_news_relation')
    op.drop_index(op.f('ix_stock_news_relation_article_id'), table_name='stock_news_relation')
    op.drop_index(op.f('ix_stock_news_relation_stock_symbol'), table_name='stock_news_relation')
    op.drop_index(op.f('ix_stock_news_relation_id'), table_name='stock_news_relation')
    op.drop_table('stock_news_relation')
    
    op.drop_index('idx_symbol_timestamp', table_name='stock_prices')
    op.drop_index(op.f('ix_stock_prices_timestamp'), table_name='stock_prices')
    op.drop_index(op.f('ix_stock_prices_symbol'), table_name='stock_prices')
    op.drop_index(op.f('ix_stock_prices_id'), table_name='stock_prices')
    op.drop_table('stock_prices')
