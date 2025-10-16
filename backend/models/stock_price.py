"""
StockPrice database model and Pydantic schemas
"""

from sqlalchemy import Column, Integer, String, DECIMAL, BigInteger, DateTime, Index
from sqlalchemy.sql import func
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from decimal import Decimal

try:
    from app.database import Base
except ImportError:
    from app.database import Base


class StockPrice(Base):
    """
    Database model for stock price data
    Stores real-time stock prices collected from brokerage APIs
    """
    __tablename__ = "stock_prices"
    __table_args__ = (
        Index('idx_symbol_timestamp', 'symbol', 'timestamp'),
        {'extend_existing': True}
    )
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    price = Column(DECIMAL(10, 2), nullable=False)
    volume = Column(BigInteger)
    open_price = Column(DECIMAL(10, 2))
    high_price = Column(DECIMAL(10, 2))
    low_price = Column(DECIMAL(10, 2))
    timestamp = Column(DateTime, nullable=False, index=True)


# Pydantic Schemas

class StockPriceBase(BaseModel):
    """Base schema with common fields"""
    symbol: str = Field(..., max_length=20)
    price: Decimal = Field(..., gt=0)
    volume: Optional[int] = None
    open_price: Optional[Decimal] = Field(None, gt=0)
    high_price: Optional[Decimal] = Field(None, gt=0)
    low_price: Optional[Decimal] = Field(None, gt=0)
    timestamp: datetime


class StockPriceCreate(StockPriceBase):
    """Schema for creating a new stock price record"""
    pass


class StockPriceUpdate(BaseModel):
    """Schema for updating a stock price record"""
    symbol: Optional[str] = Field(None, max_length=20)
    price: Optional[Decimal] = Field(None, gt=0)
    volume: Optional[int] = None
    open_price: Optional[Decimal] = Field(None, gt=0)
    high_price: Optional[Decimal] = Field(None, gt=0)
    low_price: Optional[Decimal] = Field(None, gt=0)
    timestamp: Optional[datetime] = None


class StockPriceResponse(StockPriceBase):
    """Schema for stock price responses"""
    id: int
    
    model_config = ConfigDict(from_attributes=True)
