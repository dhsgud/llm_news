"""
Auto-trading related Pydantic schemas
Data transfer objects for automated trading operations
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Literal
from decimal import Decimal


class TradingConfig(BaseModel):
    """
    Schema for trading configuration request/response
    Simplified version for API interactions
    """
    max_investment_amount: Decimal = Field(..., gt=0, description="Maximum total investment amount")
    max_position_size: Decimal = Field(..., gt=0, description="Maximum amount per position")
    risk_level: Literal["LOW", "MEDIUM", "HIGH"] = Field(..., description="Risk tolerance level")
    buy_threshold: int = Field(default=80, ge=0, le=100, description="Signal ratio to trigger buy")
    sell_threshold: int = Field(default=20, ge=0, le=100, description="Signal ratio to trigger sell")
    stop_loss_percentage: Decimal = Field(default=Decimal("5.0"), gt=0, le=100, description="Stop loss percentage")
    daily_loss_limit: Optional[Decimal] = Field(None, gt=0, description="Maximum daily loss allowed")
    trading_start_time: str = Field(default="09:00", pattern=r"^\d{2}:\d{2}$", description="Trading start time (HH:MM)")
    trading_end_time: str = Field(default="15:30", pattern=r"^\d{2}:\d{2}$", description="Trading end time (HH:MM)")
    allowed_symbols: Optional[List[str]] = Field(None, description="List of allowed stock symbols")
    excluded_symbols: Optional[List[str]] = Field(None, description="List of excluded stock symbols")
    notification_email: Optional[str] = Field(None, description="Email for notifications")
    
    class Config:
        json_schema_extra = {
            "example": {
                "max_investment_amount": 10000000.00,
                "max_position_size": 2000000.00,
                "risk_level": "MEDIUM",
                "buy_threshold": 80,
                "sell_threshold": 20,
                "stop_loss_percentage": 5.0,
                "daily_loss_limit": 500000.00,
                "trading_start_time": "09:00",
                "trading_end_time": "15:30",
                "allowed_symbols": ["005930", "000660", "035420"],
                "notification_email": "[email]"
            }
        }


class Holding(BaseModel):
    """
    Schema for a single stock holding in portfolio
    """
    symbol: str = Field(..., description="Stock symbol")
    quantity: int = Field(..., gt=0, description="Number of shares held")
    average_price: Decimal = Field(..., gt=0, description="Average purchase price per share")
    current_price: Optional[Decimal] = Field(None, gt=0, description="Current market price per share")
    total_value: Optional[Decimal] = Field(None, description="Total current value of holding")
    profit_loss: Optional[Decimal] = Field(None, description="Unrealized profit/loss")
    profit_loss_percentage: Optional[Decimal] = Field(None, description="Profit/loss percentage")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "005930",
                "quantity": 10,
                "average_price": 74000.00,
                "current_price": 75000.00,
                "total_value": 750000.00,
                "profit_loss": 10000.00,
                "profit_loss_percentage": 1.35
            }
        }


class Portfolio(BaseModel):
    """
    Schema for complete portfolio information
    """
    total_value: Decimal = Field(..., description="Total portfolio value")
    cash_balance: Decimal = Field(..., description="Available cash balance")
    invested_amount: Decimal = Field(..., description="Total amount invested in stocks")
    total_profit_loss: Decimal = Field(..., description="Total unrealized profit/loss")
    total_profit_loss_percentage: Decimal = Field(..., description="Total profit/loss percentage")
    holdings: List[Holding] = Field(default_factory=list, description="List of stock holdings")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_value": 11000000.00,
                "cash_balance": 9000000.00,
                "invested_amount": 2000000.00,
                "total_profit_loss": 50000.00,
                "total_profit_loss_percentage": 2.5,
                "holdings": [
                    {
                        "symbol": "005930",
                        "quantity": 10,
                        "average_price": 74000.00,
                        "current_price": 75000.00,
                        "total_value": 750000.00,
                        "profit_loss": 10000.00,
                        "profit_loss_percentage": 1.35
                    }
                ],
                "updated_at": "2025-10-11T14:30:00"
            }
        }


class AutoTradeStatus(BaseModel):
    """
    Schema for auto-trading system status
    """
    is_enabled: bool = Field(..., description="Whether auto-trading is enabled")
    is_running: bool = Field(..., description="Whether auto-trading is currently running")
    last_check_time: Optional[datetime] = Field(None, description="Last time system checked for signals")
    last_trade_time: Optional[datetime] = Field(None, description="Last time a trade was executed")
    total_trades_today: int = Field(default=0, description="Number of trades executed today")
    daily_profit_loss: Decimal = Field(default=Decimal("0.0"), description="Today's profit/loss")
    message: Optional[str] = Field(None, description="Status message or error")
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_enabled": True,
                "is_running": True,
                "last_check_time": "2025-10-11T14:30:00",
                "last_trade_time": "2025-10-11T10:15:00",
                "total_trades_today": 3,
                "daily_profit_loss": 25000.00,
                "message": "System running normally"
            }
        }


class TradeSignal(BaseModel):
    """
    Schema for trading signal generated by AI analysis
    """
    symbol: str = Field(..., description="Stock symbol")
    signal_ratio: int = Field(..., ge=0, le=100, description="Buy/sell signal ratio (0-100)")
    action: Literal["BUY", "SELL", "HOLD"] = Field(..., description="Recommended action")
    confidence: Decimal = Field(..., ge=0, le=1, description="Confidence level (0-1)")
    reasoning: str = Field(..., description="AI reasoning for the signal")
    generated_at: datetime = Field(..., description="Signal generation timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "005930",
                "signal_ratio": 85,
                "action": "BUY",
                "confidence": 0.82,
                "reasoning": "Strong positive sentiment with high market confidence",
                "generated_at": "2025-10-11T14:30:00"
            }
        }


class TradeExecutionRequest(BaseModel):
    """
    Schema for manual trade execution request
    """
    symbol: str = Field(..., max_length=20, description="Stock symbol")
    action: Literal["BUY", "SELL"] = Field(..., description="Trade action")
    quantity: Optional[int] = Field(None, gt=0, description="Number of shares (optional, will calculate based on config)")
    price: Optional[Decimal] = Field(None, gt=0, description="Limit price (optional for market orders)")
    order_type: Literal["MARKET", "LIMIT"] = Field(default="MARKET", description="Order type")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "005930",
                "action": "BUY",
                "quantity": 10,
                "order_type": "MARKET"
            }
        }


class TradeExecutionResponse(BaseModel):
    """
    Schema for trade execution response
    """
    success: bool = Field(..., description="Whether trade was successful")
    order_id: Optional[str] = Field(None, description="Order ID from brokerage")
    message: str = Field(..., description="Result message")
    trade_details: Optional[dict] = Field(None, description="Detailed trade information")

