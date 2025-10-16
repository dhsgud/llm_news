"""
Multi-Asset Data Models
Supports stocks, cryptocurrencies, and forex
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

try:
    from app.database import Base
except ImportError:
    from app.database import Base


class AssetType(str, enum.Enum):
    """Asset type enumeration"""
    STOCK = "stock"
    CRYPTO = "crypto"
    FOREX = "forex"


class Asset(Base):
    """Multi-asset information table"""
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    asset_type = Column(SQLEnum(AssetType), nullable=False, index=True)
    exchange = Column(String(50))  # e.g., "NASDAQ", "Binance", "Forex"
    base_currency = Column(String(10))  # For forex pairs, e.g., "USD"
    quote_currency = Column(String(10))  # For forex pairs, e.g., "KRW"
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    prices = relationship("AssetPrice", back_populates="asset", cascade="all, delete-orphan")
    sentiments = relationship("AssetSentiment", back_populates="asset", cascade="all, delete-orphan")
    holdings = relationship("AssetHolding", back_populates="asset", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_asset_type_symbol', 'asset_type', 'symbol'),
    )


class AssetPrice(Base):
    """Multi-asset price data"""
    __tablename__ = "asset_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float, nullable=False)
    volume = Column(Float)
    market_cap = Column(Float)  # For crypto
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    asset = relationship("Asset", back_populates="prices")
    
    __table_args__ = (
        Index('idx_asset_timestamp', 'asset_id', 'timestamp'),
    )


class AssetSentiment(Base):
    """Asset-specific sentiment analysis"""
    __tablename__ = "asset_sentiments"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    date = Column(DateTime, nullable=False, index=True)
    sentiment_score = Column(Float, nullable=False)  # -1.5 to +1.0
    news_count = Column(Integer, default=0)
    positive_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)
    neutral_count = Column(Integer, default=0)
    summary = Column(String(1000))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    asset = relationship("Asset", back_populates="sentiments")
    
    __table_args__ = (
        Index('idx_asset_date', 'asset_id', 'date'),
    )


class AssetHolding(Base):
    """Multi-asset portfolio holdings"""
    __tablename__ = "asset_holdings"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    average_price = Column(Float, nullable=False)
    current_price = Column(Float)
    total_value = Column(Float)
    profit_loss = Column(Float)
    profit_loss_percent = Column(Float)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    asset = relationship("Asset", back_populates="holdings")
