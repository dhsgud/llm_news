"""add backtest tables

Revision ID: 007
Revises: 006
Create Date: 2025-10-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    # Create backtest_runs table
    op.create_table(
        'backtest_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('strategy_config', sa.JSON(), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('initial_capital', sa.Float(), nullable=False),
        sa.Column('final_capital', sa.Float(), nullable=True),
        sa.Column('total_return', sa.Float(), nullable=True),
        sa.Column('total_trades', sa.Integer(), nullable=True, default=0),
        sa.Column('winning_trades', sa.Integer(), nullable=True, default=0),
        sa.Column('losing_trades', sa.Integer(), nullable=True, default=0),
        sa.Column('win_rate', sa.Float(), nullable=True),
        sa.Column('max_drawdown', sa.Float(), nullable=True),
        sa.Column('sharpe_ratio', sa.Float(), nullable=True),
        sa.Column('sortino_ratio', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True, default='PENDING'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_backtest_runs_id', 'backtest_runs', ['id'])
    op.create_index('ix_backtest_runs_user_id', 'backtest_runs', ['user_id'])
    
    # Create backtest_trades table
    op.create_table(
        'backtest_trades',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('backtest_run_id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('action', sa.String(length=10), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('signal_ratio', sa.Integer(), nullable=True),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('profit_loss', sa.Float(), nullable=True),
        sa.Column('profit_loss_percentage', sa.Float(), nullable=True),
        sa.Column('executed_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['backtest_run_id'], ['backtest_runs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_backtest_trades_id', 'backtest_trades', ['id'])
    op.create_index('ix_backtest_trades_backtest_run_id', 'backtest_trades', ['backtest_run_id'])
    
    # Create backtest_daily_stats table
    op.create_table(
        'backtest_daily_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('backtest_run_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('portfolio_value', sa.Float(), nullable=False),
        sa.Column('cash_balance', sa.Float(), nullable=False),
        sa.Column('invested_amount', sa.Float(), nullable=False),
        sa.Column('daily_return', sa.Float(), nullable=True),
        sa.Column('cumulative_return', sa.Float(), nullable=True),
        sa.Column('drawdown', sa.Float(), nullable=True),
        sa.Column('holdings', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['backtest_run_id'], ['backtest_runs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_backtest_daily_stats_id', 'backtest_daily_stats', ['id'])
    op.create_index('ix_backtest_daily_stats_backtest_run_id', 'backtest_daily_stats', ['backtest_run_id'])
    op.create_index('ix_backtest_daily_stats_date', 'backtest_daily_stats', ['date'])


def downgrade():
    op.drop_index('ix_backtest_daily_stats_date', table_name='backtest_daily_stats')
    op.drop_index('ix_backtest_daily_stats_backtest_run_id', table_name='backtest_daily_stats')
    op.drop_index('ix_backtest_daily_stats_id', table_name='backtest_daily_stats')
    op.drop_table('backtest_daily_stats')
    
    op.drop_index('ix_backtest_trades_backtest_run_id', table_name='backtest_trades')
    op.drop_index('ix_backtest_trades_id', table_name='backtest_trades')
    op.drop_table('backtest_trades')
    
    op.drop_index('ix_backtest_runs_user_id', table_name='backtest_runs')
    op.drop_index('ix_backtest_runs_id', table_name='backtest_runs')
    op.drop_table('backtest_runs')
