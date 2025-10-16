"""
SentimentAnalysis database model and Pydantic schemas
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal

try:
    from app.database import Base
except ImportError:
    from app.database import Base


class SentimentAnalysis(Base):
    """
    Database model for sentiment analysis results
    Stores AI-generated sentiment analysis for each news article
    """
    __tablename__ = "sentiment_analysis"
    __table_args__ = (
        Index('idx_article_analyzed', 'article_id', 'analyzed_at'),
        {'extend_existing': True}
    )
    
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("news_articles.id", ondelete="CASCADE"), nullable=False, index=True)
    sentiment = Column(String(20), nullable=False)  # 'Positive', 'Negative', 'Neutral'
    score = Column(Float, nullable=False)  # -1.5 to 1.0
    reasoning = Column(Text)
    analyzed_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    # Relationship to NewsArticle
    # article = relationship("NewsArticle", backref="sentiment_analyses")


# Pydantic Schemas

SentimentType = Literal["Positive", "Negative", "Neutral"]


class SentimentAnalysisBase(BaseModel):
    """Base schema with common fields"""
    article_id: int
    sentiment: SentimentType
    score: float = Field(..., ge=-1.5, le=1.0, description="Sentiment score from -1.5 to 1.0")
    reasoning: Optional[str] = None


class SentimentAnalysisCreate(SentimentAnalysisBase):
    """Schema for creating a new sentiment analysis"""
    pass


class SentimentAnalysisUpdate(BaseModel):
    """Schema for updating a sentiment analysis"""
    sentiment: Optional[SentimentType] = None
    score: Optional[float] = Field(None, ge=-1.5, le=1.0)
    reasoning: Optional[str] = None


class SentimentAnalysisResponse(SentimentAnalysisBase):
    """Schema for sentiment analysis responses"""
    id: int
    analyzed_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class SentimentResult(BaseModel):
    """
    Schema for LLM sentiment analysis result
    Used for internal processing
    """
    article_id: int
    sentiment: SentimentType
    score: float
    reasoning: str
    analyzed_at: datetime = Field(default_factory=datetime.now)
