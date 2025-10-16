"""
StockNewsRelation database model and Pydantic schemas
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Index
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

try:
    from app.database import Base
except ImportError:
    from app.database import Base


class StockNewsRelation(Base):
    """
    Database model for stock-news relationships
    Links news articles to specific stock symbols with relevance scores
    """
    __tablename__ = "stock_news_relation"
    __table_args__ = (
        Index('idx_stock_article', 'stock_symbol', 'article_id'),
        {'extend_existing': True}
    )
    
    id = Column(Integer, primary_key=True, index=True)
    stock_symbol = Column(String(20), nullable=False, index=True)
    article_id = Column(Integer, ForeignKey('news_articles.id'), nullable=False, index=True)
    relevance_score = Column(Float)


# Pydantic Schemas

class StockNewsRelationBase(BaseModel):
    """Base schema with common fields"""
    stock_symbol: str = Field(..., max_length=20)
    article_id: int
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0)


class StockNewsRelationCreate(StockNewsRelationBase):
    """Schema for creating a new stock-news relation"""
    pass


class StockNewsRelationUpdate(BaseModel):
    """Schema for updating a stock-news relation"""
    stock_symbol: Optional[str] = Field(None, max_length=20)
    article_id: Optional[int] = None
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0)


class StockNewsRelationResponse(StockNewsRelationBase):
    """Schema for stock-news relation responses"""
    id: int
    
    model_config = ConfigDict(from_attributes=True)
