"""
NewsArticle database model and Pydantic schemas
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from sqlalchemy.sql import func
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

try:
    from app.database import Base
except ImportError:
    from app.database import Base


class NewsArticle(Base):
    """
    Database model for news articles
    Stores financial news collected from external APIs
    """
    __tablename__ = "news_articles"
    __table_args__ = (
        Index('idx_published_asset', 'published_date', 'asset_type'),
        {'extend_existing': True}
    )
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    author = Column(String(200), nullable=True)
    published_date = Column(DateTime, nullable=False, index=True)
    source = Column(String(100))
    url = Column(String(500))
    asset_type = Column(String(50), default="general", index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)


# Pydantic Schemas

class NewsArticleBase(BaseModel):
    """Base schema with common fields"""
    title: str = Field(..., max_length=500)
    content: str
    description: Optional[str] = None
    author: Optional[str] = Field(None, max_length=200)
    published_date: datetime
    source: str = Field(..., max_length=100)
    url: Optional[str] = Field(None, max_length=500)
    asset_type: str = Field(default="general", max_length=50)


class NewsArticleCreate(NewsArticleBase):
    """Schema for creating a new news article"""
    pass


class NewsArticleUpdate(BaseModel):
    """Schema for updating a news article"""
    title: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = Field(None, max_length=200)
    published_date: Optional[datetime] = None
    source: Optional[str] = Field(None, max_length=100)
    url: Optional[str] = Field(None, max_length=500)
    asset_type: Optional[str] = Field(None, max_length=50)


class NewsArticleResponse(NewsArticleBase):
    """Schema for news article responses"""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
