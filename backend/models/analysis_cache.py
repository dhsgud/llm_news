"""
AnalysisCache database model and Pydantic schemas
"""

from sqlalchemy import Column, Integer, String, DateTime, Index, JSON
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any, Dict

try:
    from app.database import Base
    from config import settings
except ImportError:
    from app.database import Base
    from config import settings


class AnalysisCache(Base):
    """
    Database model for caching analysis results
    Stores computed analysis results to avoid redundant LLM calls
    """
    __tablename__ = "analysis_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    cache_key = Column(String(100), unique=True, nullable=False, index=True)
    result_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_key_expires', 'cache_key', 'expires_at'),
    )


# Pydantic Schemas

class AnalysisCacheBase(BaseModel):
    """Base schema with common fields"""
    cache_key: str = Field(..., max_length=100)
    result_json: Dict[str, Any]


class AnalysisCacheCreate(AnalysisCacheBase):
    """Schema for creating a new cache entry"""
    expires_at: Optional[datetime] = None
    
    def set_expiry(self) -> datetime:
        """Calculate expiry time based on settings"""
        if self.expires_at is None:
            self.expires_at = datetime.now() + timedelta(hours=settings.cache_expiry_hours)
        return self.expires_at


class AnalysisCacheUpdate(BaseModel):
    """Schema for updating a cache entry"""
    result_json: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None


class AnalysisCacheResponse(AnalysisCacheBase):
    """Schema for cache responses"""
    id: int
    created_at: datetime
    expires_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return datetime.now() > self.expires_at
