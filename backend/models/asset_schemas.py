"""
Pydantic schemas for multi-asset support
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class AssetType(str, Enum):
    """Asset type enumeration"""
    STOCK = "stock"
    CRYPTO = "crypto"
    FOREX = "forex"


class AssetBase(BaseModel):
    """Base asset schema"""
    symbol: str = Field(..., max_length=20)
    name: str = Field(..., max_length=200)
    asset_type: AssetType
    exchange: Optional[str] = Field(None, max_length=50)
    base_currency: Optional[str] = Field(None, max_length=10)
    quote_currency: Optional[str] = Field(None, max_length=10)


class AssetCreate(AssetBase):
    """Schema for creating an asset"""
    pass


class AssetResponse(AssetBase):
    """Schema for asset response"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AssetPriceBase(BaseModel):
    """Base price schema"""
    timestamp: datetime
    open_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    close_price: float
    volume: Optional[float] = None
    market_cap: Optional[float] = None


class AssetPriceResponse(AssetPriceBase):
    """Schema for price response"""
    id: int
    asset_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class AssetSentimentResponse(BaseModel):
    """Schema for sentiment response"""
    id: int
    asset_id: int
    date: datetime
    sentiment_score: float
    news_count: int
    positive_count: int
    negative_count: int
    neutral_count: int
    summary: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class AssetHoldingResponse(BaseModel):
    """Schema for holding response"""
    id: int
    asset_id: int
    asset: AssetResponse
    quantity: float
    average_price: float
    current_price: Optional[float] = None
    total_value: Optional[float] = None
    profit_loss: Optional[float] = None
    profit_loss_percent: Optional[float] = None
    last_updated: datetime
    
    class Config:
        from_attributes = True


class AssetDetailResponse(AssetResponse):
    """Detailed asset information with latest price and sentiment"""
    latest_price: Optional[AssetPriceResponse] = None
    latest_sentiment: Optional[AssetSentimentResponse] = None
    price_change_24h: Optional[float] = None
    price_change_percent_24h: Optional[float] = None


class PortfolioSummary(BaseModel):
    """Portfolio summary across all asset types"""
    total_value: float
    total_profit_loss: float
    total_profit_loss_percent: float
    stock_value: float
    crypto_value: float
    forex_value: float
    holdings: List[AssetHoldingResponse]
