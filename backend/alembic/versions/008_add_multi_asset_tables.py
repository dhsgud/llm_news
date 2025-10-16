"""add multi-asset tables

Revision ID: 008
Revises: 007
Create Date: 2025-10-16

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    # Create assets table
    op.create_table(
        'assets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('asset_type', sa.Enum('stock', 'crypto', 'forex', name='assettype'), nullable=False),
        sa.Column('exchange', sa.String(50), nullable=True),
        sa.Column('base_currency', sa.String(10), nullable=True),
        sa.Column('quote_currency', sa.String(10), nullable=True),
        sa.Column('is_active', sa.Integer(), default=1),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_assets_id', 'assets', ['id'])
    op.create_index('ix_assets_symbol', 'assets', ['symbol'], unique=True)
    op.create_index('ix_assets_asset_type', 'assets', ['asset_type'])
    op.create_index('idx_asset_type_symbol', 'assets', ['asset_type', 'symbol'])
    
    # Create asset_prices table
    op.create_table(
        'asset_prices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('asset_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('open_price', sa.Float(), nullable=True),
        sa.Column('high_price', sa.Float(), nullable=True),
        sa.Column('low_price', sa.Float(), nullable=True),
        sa.Column('close_price', sa.Float(), nullable=False),
        sa.Column('volume', sa.Float(), nullable=True),
        sa.Column('market_cap', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_asset_prices_id', 'asset_prices', ['id'])
    op.create_index('ix_asset_prices_timestamp', 'asset_prices', ['timestamp'])
    op.create_index('idx_asset_timestamp', 'asset_prices', ['asset_id', 'timestamp'])
    
    # Create asset_sentiments table
    op.create_table(
        'asset_sentiments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('asset_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('sentiment_score', sa.Float(), nullable=False),
        sa.Column('news_count', sa.Integer(), default=0),
        sa.Column('positive_count', sa.Integer(), default=0),
        sa.Column('negative_count', sa.Integer(), default=0),
        sa.Column('neutral_count', sa.Integer(), default=0),
        sa.Column('summary', sa.String(1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_asset_sentiments_id', 'asset_sentiments', ['id'])
    op.create_index('ix_asset_sentiments_date', 'asset_sentiments', ['date'])
    op.create_index('idx_asset_date', 'asset_sentiments', ['asset_id', 'date'])
    
    # Create asset_holdings table
    op.create_table(
        'asset_holdings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('asset_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('average_price', sa.Float(), nullable=False),
        sa.Column('current_price', sa.Float(), nullable=True),
        sa.Column('total_value', sa.Float(), nullable=True),
        sa.Column('profit_loss', sa.Float(), nullable=True),
        sa.Column('profit_loss_percent', sa.Float(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_asset_holdings_id', 'asset_holdings', ['id'])


def downgrade():
    op.drop_index('ix_asset_holdings_id', table_name='asset_holdings')
    op.drop_table('asset_holdings')
    
    op.drop_index('idx_asset_date', table_name='asset_sentiments')
    op.drop_index('ix_asset_sentiments_date', table_name='asset_sentiments')
    op.drop_index('ix_asset_sentiments_id', table_name='asset_sentiments')
    op.drop_table('asset_sentiments')
    
    op.drop_index('idx_asset_timestamp', table_name='asset_prices')
    op.drop_index('ix_asset_prices_timestamp', table_name='asset_prices')
    op.drop_index('ix_asset_prices_id', table_name='asset_prices')
    op.drop_table('asset_prices')
    
    op.drop_index('idx_asset_type_symbol', table_name='assets')
    op.drop_index('ix_assets_asset_type', table_name='assets')
    op.drop_index('ix_assets_symbol', table_name='assets')
    op.drop_index('ix_assets_id', table_name='assets')
    op.drop_table('assets')
    
    sa.Enum(name='assettype').drop(op.get_bind(), checkfirst=False)
