"""
AccountHolding database model and Pydantic schemas
"""

from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, Index
from sqlalchemy.sql import func
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from decimal import Decimal

try:
    from app.database import Base
except ImportError:
    from app.database import Base


class AccountHolding(Base):
    """
    Database model for account holdings
    Stores current stock positions in the trading account
    """
    __tablename__ = "account_holdings"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    average_price = Column(DECIMAL(10, 2), nullable=False)
    current_price = Column(DECIMAL(10, 2))
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


# Pydantic Schemas

class AccountHoldingBase(BaseModel):
    """Base schema with common fields"""
    symbol: str = Field(..., max_length=20)
    quantity: int = Field(..., gt=0)
    average_price: Decimal = Field(..., gt=0)
    current_price: Optional[Decimal] = Field(None, gt=0)


class AccountHoldingCreate(AccountHoldingBase):
    """Schema for creating a new account holding"""
    pass


class AccountHoldingUpdate(BaseModel):
    """Schema for updating an account holding"""
    symbol: Optional[str] = Field(None, max_length=20)
    quantity: Optional[int] = Field(None, gt=0)
    average_price: Optional[Decimal] = Field(None, gt=0)
    current_price: Optional[Decimal] = Field(None, gt=0)


class AccountHoldingResponse(AccountHoldingBase):
    """Schema for account holding responses"""
    id: int
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
