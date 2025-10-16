"""
AutoTradeConfig database model and Pydantic schemas
Stores configuration for automated trading system
"""

from sqlalchemy import Column, Integer, String, DECIMAL, Boolean, DateTime, Text
from sqlalchemy.sql import func
from datetime import datetime, time
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal
from decimal import Decimal

try:
    from app.database import Base
except ImportError:
    from app.database import Base


class AutoTradeConfig(Base):
    """
    Database model for auto-trading configuration
    Stores user preferences and risk parameters for automated trading
    """
    __tablename__ = "auto_trade_config"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), unique=True, nullable=False, index=True)  # For multi-user support
    is_enabled = Column(Boolean, default=False, nullable=False)
    max_investment_amount = Column(DECIMAL(15, 2), nullable=False)  # Maximum total investment
    max_position_size = Column(DECIMAL(15, 2), nullable=False)  # Maximum per position
    risk_level = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH
    buy_threshold = Column(Integer, default=80, nullable=False)  # Signal ratio to trigger buy (0-100)
    sell_threshold = Column(Integer, default=20, nullable=False)  # Signal ratio to trigger sell (0-100)
    stop_loss_percentage = Column(DECIMAL(5, 2), default=5.0, nullable=False)  # Stop loss %
    daily_loss_limit = Column(DECIMAL(15, 2))  # Maximum daily loss allowed
    trading_start_time = Column(String(5), default="09:00")  # Trading hours start (HH:MM)
    trading_end_time = Column(String(5), default="15:30")  # Trading hours end (HH:MM)
    allowed_symbols = Column(Text)  # Comma-separated list of allowed stock symbols
    excluded_symbols = Column(Text)  # Comma-separated list of excluded stock symbols
    notification_email = Column(String(255))  # Email for trade notifications
    notification_enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


# Pydantic Schemas

class AutoTradeConfigBase(BaseModel):
    """Base schema with common fields"""
    user_id: str = Field(..., max_length=100)
    is_enabled: bool = False
    max_investment_amount: Decimal = Field(..., gt=0)
    max_position_size: Decimal = Field(..., gt=0)
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    buy_threshold: int = Field(default=80, ge=0, le=100)
    sell_threshold: int = Field(default=20, ge=0, le=100)
    stop_loss_percentage: Decimal = Field(default=Decimal("5.0"), gt=0, le=100)
    daily_loss_limit: Optional[Decimal] = Field(None, gt=0)
    trading_start_time: str = Field(default="09:00", pattern=r"^\d{2}:\d{2}$")
    trading_end_time: str = Field(default="15:30", pattern=r"^\d{2}:\d{2}$")
    allowed_symbols: Optional[str] = None
    excluded_symbols: Optional[str] = None
    notification_email: Optional[str] = Field(None, max_length=255)
    notification_enabled: bool = True


class AutoTradeConfigCreate(AutoTradeConfigBase):
    """Schema for creating a new auto-trade configuration"""
    pass


class AutoTradeConfigUpdate(BaseModel):
    """Schema for updating auto-trade configuration"""
    is_enabled: Optional[bool] = None
    max_investment_amount: Optional[Decimal] = Field(None, gt=0)
    max_position_size: Optional[Decimal] = Field(None, gt=0)
    risk_level: Optional[Literal["LOW", "MEDIUM", "HIGH"]] = None
    buy_threshold: Optional[int] = Field(None, ge=0, le=100)
    sell_threshold: Optional[int] = Field(None, ge=0, le=100)
    stop_loss_percentage: Optional[Decimal] = Field(None, gt=0, le=100)
    daily_loss_limit: Optional[Decimal] = Field(None, gt=0)
    trading_start_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    trading_end_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    allowed_symbols: Optional[str] = None
    excluded_symbols: Optional[str] = None
    notification_email: Optional[str] = Field(None, max_length=255)
    notification_enabled: Optional[bool] = None


class AutoTradeConfigResponse(AutoTradeConfigBase):
    """Schema for auto-trade configuration responses"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

