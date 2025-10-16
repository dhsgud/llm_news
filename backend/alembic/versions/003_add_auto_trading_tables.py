"""Add auto trading tables: TradeHistory, AutoTradeConfig

Revision ID: 003
Revises: 002
Create Date: 2025-10-11 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create trade_history table
    op.create_table(
        'trade_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.String(length=100), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('trade_type', sa.String(length=10), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('executed_price', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('total_amount', sa.DECIMAL(precision=15, scale=2), nullable=False),
        sa.Column('executed_at', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('signal_ratio', sa.Integer(), nullable=True),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_id')
    )
    op.create_index(op.f('ix_trade_history_id'), 'trade_history', ['id'], unique=False)
    op.create_index(op.f('ix_trade_history_order_id'), 'trade_history', ['order_id'], unique=True)
    op.create_index('idx_trade_symbol', 'trade_history', ['symbol'], unique=False)
    op.create_index('idx_trade_executed_at', 'trade_history', ['executed_at'], unique=False)
    op.create_index('idx_trade_type', 'trade_history', ['trade_type'], unique=False)

    # Create auto_trade_config table
    op.create_table(
        'auto_trade_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('max_investment_amount', sa.DECIMAL(precision=15, scale=2), nullable=False),
        sa.Column('max_position_size', sa.DECIMAL(precision=15, scale=2), nullable=False),
        sa.Column('risk_level', sa.String(length=20), nullable=False),
        sa.Column('buy_threshold', sa.Integer(), nullable=False, server_default='80'),
        sa.Column('sell_threshold', sa.Integer(), nullable=False, server_default='20'),
        sa.Column('stop_loss_percentage', sa.DECIMAL(precision=5, scale=2), nullable=False, server_default='5.0'),
        sa.Column('daily_loss_limit', sa.DECIMAL(precision=15, scale=2), nullable=True),
        sa.Column('trading_start_time', sa.String(length=5), nullable=True, server_default='09:00'),
        sa.Column('trading_end_time', sa.String(length=5), nullable=True, server_default='15:30'),
        sa.Column('allowed_symbols', sa.Text(), nullable=True),
        sa.Column('excluded_symbols', sa.Text(), nullable=True),
        sa.Column('notification_email', sa.String(length=255), nullable=True),
        sa.Column('notification_enabled', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_auto_trade_config_id'), 'auto_trade_config', ['id'], unique=False)
    op.create_index(op.f('ix_auto_trade_config_user_id'), 'auto_trade_config', ['user_id'], unique=True)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_auto_trade_config_user_id'), table_name='auto_trade_config')
    op.drop_index(op.f('ix_auto_trade_config_id'), table_name='auto_trade_config')
    op.drop_table('auto_trade_config')
    
    op.drop_index('idx_trade_type', table_name='trade_history')
    op.drop_index('idx_trade_executed_at', table_name='trade_history')
    op.drop_index('idx_trade_symbol', table_name='trade_history')
    op.drop_index(op.f('ix_trade_history_order_id'), table_name='trade_history')
    op.drop_index(op.f('ix_trade_history_id'), table_name='trade_history')
    op.drop_table('trade_history')

