"""
Social Media database models and Pydantic schemas
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Index, Boolean
from sqlalchemy.sql import func
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, HttpUrl
from typing import Optional, Literal

try:
    from app.database import Base
except ImportError:
    from app.database import Base


class SocialPost(Base):
    """
    Database model for social media posts (Twitter/Reddit)
    """
    __tablename__ = "social_posts"
    __table_args__ = (
        Index('idx_social_symbol_created', 'symbol', 'created_at'),
        Index('idx_social_platform_created', 'platform', 'created_at'),
        {'extend_existing': True}
    )
    
    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(20), nullable=False)  # 'twitter', 'reddit'
    post_id = Column(String(100), unique=True, nullable=False, index=True)
    symbol = Column(String(20), nullable=True, index=True)  # Stock symbol if mentioned
    author = Column(String(100))
    content = Column(Text, nullable=False)
    url = Column(String(500))
    likes = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    created_at = Column(DateTime, nullable=False, index=True)
    collected_at = Column(DateTime, default=func.now(), nullable=False)


class SocialSentiment(Base):
    """
    Database model for social media sentiment analysis
    """
    __tablename__ = "social_sentiments"
    __table_args__ = (
        Index('idx_social_sentiment_post', 'post_id', 'analyzed_at'),
        {'extend_existing': True}
    )
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("social_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    sentiment = Column(String(20), nullable=False)  # 'Positive', 'Negative', 'Neutral'
    score = Column(Float, nullable=False)  # -1.5 to 1.0
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    reasoning = Column(Text)
    analyzed_at = Column(DateTime, default=func.now(), nullable=False, index=True)


class AggregatedSocialSentiment(Base):
    """
    Database model for aggregated social sentiment by symbol and time period
    """
    __tablename__ = "aggregated_social_sentiments"
    __table_args__ = (
        Index('idx_agg_social_symbol_date', 'symbol', 'date'),
        {'extend_existing': True}
    )
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=True, index=True)
    date = Column(DateTime, nullable=False, index=True)
    platform = Column(String(20), nullable=False)
    post_count = Column(Integer, default=0)
    avg_sentiment_score = Column(Float, default=0.0)
    positive_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)
    neutral_count = Column(Integer, default=0)
    total_engagement = Column(Integer, default=0)  # likes + shares + comments
    created_at = Column(DateTime, default=func.now(), nullable=False)


# Pydantic Schemas

PlatformType = Literal["twitter", "reddit"]
SentimentType = Literal["Positive", "Negative", "Neutral"]


class SocialPostBase(BaseModel):
    """Base schema for social posts"""
    platform: PlatformType
    post_id: str
    symbol: Optional[str] = None
    author: Optional[str] = None
    content: str
    url: Optional[str] = None
    likes: int = 0
    shares: int = 0
    comments: int = 0
    created_at: datetime


class SocialPostCreate(SocialPostBase):
    """Schema for creating a social post"""
    pass


class SocialPostResponse(SocialPostBase):
    """Schema for social post responses"""
    id: int
    collected_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class SocialSentimentBase(BaseModel):
    """Base schema for social sentiment"""
    post_id: int
    sentiment: SentimentType
    score: float = Field(..., ge=-1.5, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: Optional[str] = None


class SocialSentimentCreate(SocialSentimentBase):
    """Schema for creating social sentiment"""
    pass


class SocialSentimentResponse(SocialSentimentBase):
    """Schema for social sentiment responses"""
    id: int
    analyzed_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AggregatedSocialSentimentResponse(BaseModel):
    """Schema for aggregated social sentiment"""
    id: int
    symbol: Optional[str]
    date: datetime
    platform: PlatformType
    post_count: int
    avg_sentiment_score: float
    positive_count: int
    negative_count: int
    neutral_count: int
    total_engagement: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class SocialSentimentSummary(BaseModel):
    """Summary of social sentiment for a symbol"""
    symbol: Optional[str]
    platform: PlatformType
    total_posts: int
    avg_sentiment: float
    sentiment_distribution: dict[str, int]
    total_engagement: int
    trending_score: float  # Weighted by engagement
