"""
TradeHistory database model and Pydantic schemas
Stores all executed trades for tracking and analysis
"""

from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, Text, Index
from sqlalchemy.sql import func
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal
from decimal import Decimal

try:
    from app.database import Base
except ImportError:
    from app.database import Base


class TradeHistory(Base):
    """
    Database model for trade history
    Records all executed trades with full details
    """
    __tablename__ = "trade_history"
    __table_args__ = (
        Index('idx_trade_symbol', 'symbol'),
        Index('idx_trade_executed_at', 'executed_at'),
        Index('idx_trade_type', 'trade_type'),
        Index('idx_trade_user_id', 'user_id'),
        {'extend_existing': True}
    )
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)  # User identifier
    order_id = Column(String(100), unique=True, nullable=True, index=True)  # Brokerage order ID
    symbol = Column(String(20), nullable=False, index=True)
    action = Column(String(10), nullable=False)  # BUY or SELL (alias for trade_type)
    trade_type = Column(String(10), nullable=False)  # BUY or SELL
    quantity = Column(Integer, nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)  # Executed price per share
    executed_price = Column(DECIMAL(10, 2), nullable=False)  # Executed price per share
    total_amount = Column(DECIMAL(15, 2), nullable=False)
    profit_loss = Column(DECIMAL(15, 2), default=Decimal("0.0"))  # Realized profit/loss
    executed_at = Column(DateTime, nullable=False, index=True)
    status = Column(String(20), nullable=False)  # COMPLETED, FAILED, PENDING, PARTIAL
    signal_ratio = Column(Integer)  # AI signal ratio that triggered this trade (0-100)
    reasoning = Column(Text)  # AI reasoning for the trade
    message = Column(Text)  # Additional information or error message
    created_at = Column(DateTime, default=func.now(), nullable=False)


# Pydantic Schemas

class TradeHistoryBase(BaseModel):
    """Base schema with common fields"""
    order_id: str = Field(..., max_length=100)
    symbol: str = Field(..., max_length=20)
    trade_type: Literal["BUY", "SELL"]
    quantity: int = Field(..., gt=0)
    executed_price: Decimal = Field(..., gt=0)
    total_amount: Decimal
    executed_at: datetime
    status: Literal["SUCCESS", "FAILED", "PENDING", "PARTIAL"]
    signal_ratio: Optional[int] = Field(None, ge=0, le=100)
    reasoning: Optional[str] = None
    message: Optional[str] = None


class TradeHistoryCreate(TradeHistoryBase):
    """Schema for creating a new trade history record"""
    pass


class TradeHistoryUpdate(BaseModel):
    """Schema for updating a trade history record"""
    status: Optional[Literal["SUCCESS", "FAILED", "PENDING", "PARTIAL"]] = None
    message: Optional[str] = None


class TradeHistoryResponse(TradeHistoryBase):
    """Schema for trade history responses"""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

