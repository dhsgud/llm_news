"""
Backtesting Pydantic Schemas
Data transfer objects for backtesting operations
Requirements: Task 27
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from decimal import Decimal


class BacktestStrategyConfig(BaseModel):
    """Configuration for backtesting strategy"""
    buy_threshold: int = Field(default=80, ge=0, le=100, description="Signal ratio to trigger buy")
    sell_threshold: int = Field(default=20, ge=0, le=100, description="Signal ratio to trigger sell")
    max_position_size: Decimal = Field(..., gt=0, description="Maximum amount per position")
    stop_loss_percentage: Decimal = Field(default=Decimal("5.0"), gt=0, le=100, description="Stop loss percentage")
    risk_level: Literal["LOW", "MEDIUM", "HIGH"] = Field(default="MEDIUM", description="Risk tolerance level")
    symbols: Optional[List[str]] = Field(None, description="Specific symbols to trade (None = all available)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "buy_threshold": 80,
                "sell_threshold": 20,
                "max_position_size": 2000000.00,
                "stop_loss_percentage": 5.0,
                "risk_level": "MEDIUM",
                "symbols": ["005930", "000660"]
            }
        }


class BacktestRequest(BaseModel):
    """Request to start a backtest"""
    name: str = Field(..., max_length=200, description="Name for this backtest run")
    description: Optional[str] = Field(None, description="Description of the backtest")
    start_date: datetime = Field(..., description="Start date for backtest period")
    end_date: datetime = Field(..., description="End date for backtest period")
    initial_capital: Decimal = Field(..., gt=0, description="Initial capital amount")
    strategy_config: BacktestStrategyConfig = Field(..., description="Strategy configuration")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Conservative Strategy Test",
                "description": "Testing conservative strategy with 80/20 thresholds",
                "start_date": "2024-01-01T00:00:00",
                "end_date": "2024-12-31T23:59:59",
                "initial_capital": 10000000.00,
                "strategy_config": {
                    "buy_threshold": 80,
                    "sell_threshold": 20,
                    "max_position_size": 2000000.00,
                    "stop_loss_percentage": 5.0,
                    "risk_level": "MEDIUM"
                }
            }
        }


class BacktestTradeResult(BaseModel):
    """Individual trade result from backtest"""
    symbol: str
    action: str
    quantity: int
    price: float
    total_amount: float
    signal_ratio: Optional[int] = None
    reasoning: Optional[str] = None
    profit_loss: Optional[float] = None
    profit_loss_percentage: Optional[float] = None
    executed_at: datetime


class BacktestDailyStatsResult(BaseModel):
    """Daily statistics from backtest"""
    date: datetime
    portfolio_value: float
    cash_balance: float
    invested_amount: float
    daily_return: Optional[float] = None
    cumulative_return: Optional[float] = None
    drawdown: Optional[float] = None
    holdings: Optional[List[Dict[str, Any]]] = None


class BacktestMetrics(BaseModel):
    """Performance metrics from backtest"""
    initial_capital: float
    final_capital: float
    total_return: float
    total_return_percentage: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    max_drawdown: float
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    average_win: Optional[float] = None
    average_loss: Optional[float] = None
    profit_factor: Optional[float] = None


class BacktestResult(BaseModel):
    """Complete backtest result"""
    id: int
    name: str
    description: Optional[str] = None
    status: str
    start_date: datetime
    end_date: datetime
    strategy_config: Dict[str, Any]
    metrics: Optional[BacktestMetrics] = None
    trades: List[BacktestTradeResult] = []
    daily_stats: List[BacktestDailyStatsResult] = []
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class BacktestSummary(BaseModel):
    """Summary of a backtest run (without detailed trades/stats)"""
    id: int
    name: str
    description: Optional[str] = None
    status: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: Optional[float] = None
    total_return: Optional[float] = None
    total_trades: int
    win_rate: Optional[float] = None
    max_drawdown: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class BacktestComparison(BaseModel):
    """Comparison between multiple backtest runs"""
    backtests: List[BacktestSummary]
    best_return: Optional[int] = Field(None, description="ID of backtest with best return")
    best_sharpe: Optional[int] = Field(None, description="ID of backtest with best Sharpe ratio")
    lowest_drawdown: Optional[int] = Field(None, description="ID of backtest with lowest drawdown")
