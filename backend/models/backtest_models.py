"""
Backtesting Models
Database models for backtesting framework
Requirements: Task 27
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

try:
    from app.database import Base
except ImportError:
    from app.database import Base


class BacktestRun(Base):
    """
    Represents a single backtest execution
    """
    __tablename__ = "backtest_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Strategy configuration
    strategy_config = Column(JSON, nullable=False)  # Trading strategy parameters
    
    # Time period
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    # Initial conditions
    initial_capital = Column(Float, nullable=False)
    
    # Results
    final_capital = Column(Float, nullable=True)
    total_return = Column(Float, nullable=True)  # Percentage
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, nullable=True)  # Percentage
    
    # Risk metrics
    max_drawdown = Column(Float, nullable=True)  # Percentage
    sharpe_ratio = Column(Float, nullable=True)
    sortino_ratio = Column(Float, nullable=True)
    
    # Status
    status = Column(String(50), default="PENDING")  # PENDING, RUNNING, COMPLETED, FAILED
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    trades = relationship("BacktestTrade", back_populates="backtest_run", cascade="all, delete-orphan")
    daily_stats = relationship("BacktestDailyStats", back_populates="backtest_run", cascade="all, delete-orphan")


class BacktestTrade(Base):
    """
    Individual trade executed during backtest
    """
    __tablename__ = "backtest_trades"
    
    id = Column(Integer, primary_key=True, index=True)
    backtest_run_id = Column(Integer, ForeignKey("backtest_runs.id"), nullable=False, index=True)
    
    # Trade details
    symbol = Column(String(20), nullable=False)
    action = Column(String(10), nullable=False)  # BUY, SELL
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    
    # Signal information
    signal_ratio = Column(Integer, nullable=True)
    reasoning = Column(Text, nullable=True)
    
    # Results (for sells)
    profit_loss = Column(Float, nullable=True)
    profit_loss_percentage = Column(Float, nullable=True)
    
    # Timestamp
    executed_at = Column(DateTime, nullable=False)
    
    # Relationships
    backtest_run = relationship("BacktestRun", back_populates="trades")


class BacktestDailyStats(Base):
    """
    Daily statistics during backtest period
    """
    __tablename__ = "backtest_daily_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    backtest_run_id = Column(Integer, ForeignKey("backtest_runs.id"), nullable=False, index=True)
    
    date = Column(DateTime, nullable=False, index=True)
    
    # Portfolio values
    portfolio_value = Column(Float, nullable=False)
    cash_balance = Column(Float, nullable=False)
    invested_amount = Column(Float, nullable=False)
    
    # Daily metrics
    daily_return = Column(Float, nullable=True)  # Percentage
    cumulative_return = Column(Float, nullable=True)  # Percentage
    drawdown = Column(Float, nullable=True)  # Percentage from peak
    
    # Holdings snapshot
    holdings = Column(JSON, nullable=True)  # List of current holdings
    
    # Relationships
    backtest_run = relationship("BacktestRun", back_populates="daily_stats")
