"""
Cache Service Module
Handles caching of analysis results with expiration logic
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

try:
    from models import AnalysisCache, AnalysisCacheCreate
    from config import settings
except ImportError:
    from models import AnalysisCache, AnalysisCacheCreate
    from config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """
    Service for caching analysis results
    
    Provides methods to:
    - Store analysis results with automatic expiration
    - Retrieve cached results if not expired
    - Clean up expired cache entries
    """
    
    def __init__(self, expiry_hours: Optional[int] = None):
        """
        Initialize cache service
        
        Args:
            expiry_hours: Cache expiry time in hours (default from settings)
        """
        self.expiry_hours = expiry_hours or settings.cache_expiry_hours
        logger.info(f"CacheService initialized with {self.expiry_hours}h expiry")
    
    def get(
        self,
        db: Session,
        cache_key: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached result if exists and not expired
        
        Args:
            db: Database session
            cache_key: Unique cache key
            
        Returns:
            Cached result dictionary or None if not found/expired
        """
        logger.debug(f"Checking cache for key: {cache_key}")
        
        # Query cache entry
        cache_entry = db.query(AnalysisCache).filter(
            AnalysisCache.cache_key == cache_key
        ).first()
        
        if not cache_entry:
            logger.debug(f"Cache miss: {cache_key}")
            return None
        
        # Check if expired
        if datetime.now() > cache_entry.expires_at:
            logger.info(f"Cache expired: {cache_key}")
            # Delete expired entry
            db.delete(cache_entry)
            db.commit()
            return None
        
        logger.info(f"Cache hit: {cache_key}")
        return cache_entry.result_json
    
    def set(
        self,
        db: Session,
        cache_key: str,
        result: Dict[str, Any],
        expiry_hours: Optional[int] = None
    ) -> AnalysisCache:
        """
        Store result in cache with expiration
        
        Args:
            db: Database session
            cache_key: Unique cache key
            result: Result dictionary to cache
            expiry_hours: Optional custom expiry time (uses default if None)
            
        Returns:
            Created AnalysisCache object
        """
        logger.info(f"Caching result for key: {cache_key}")
        
        # Calculate expiry time
        expiry_time = datetime.now() + timedelta(
            hours=expiry_hours or self.expiry_hours
        )
        
        # Check if entry already exists
        existing = db.query(AnalysisCache).filter(
            AnalysisCache.cache_key == cache_key
        ).first()
        
        if existing:
            # Update existing entry
            logger.debug(f"Updating existing cache entry: {cache_key}")
            existing.result_json = result
            existing.created_at = datetime.now()
            existing.expires_at = expiry_time
            db.commit()
            db.refresh(existing)
            return existing
        
        # Create new cache entry
        cache_data = AnalysisCacheCreate(
            cache_key=cache_key,
            result_json=result,
            expires_at=expiry_time
        )
        
        cache_entry = AnalysisCache(**cache_data.model_dump())
        db.add(cache_entry)
        db.commit()
        db.refresh(cache_entry)
        
        logger.debug(f"Created new cache entry: {cache_key}, expires at {expiry_time}")
        return cache_entry
    
    def delete(
        self,
        db: Session,
        cache_key: str
    ) -> bool:
        """
        Delete cache entry
        
        Args:
            db: Database session
            cache_key: Cache key to delete
            
        Returns:
            True if deleted, False if not found
        """
        logger.debug(f"Deleting cache entry: {cache_key}")
        
        cache_entry = db.query(AnalysisCache).filter(
            AnalysisCache.cache_key == cache_key
        ).first()
        
        if cache_entry:
            db.delete(cache_entry)
            db.commit()
            logger.info(f"Cache entry deleted: {cache_key}")
            return True
        
        logger.debug(f"Cache entry not found: {cache_key}")
        return False
    
    def cleanup_expired(
        self,
        db: Session
    ) -> int:
        """
        Clean up all expired cache entries
        
        Args:
            db: Database session
            
        Returns:
            Number of entries deleted
        """
        logger.info("Cleaning up expired cache entries")
        
        # Find all expired entries
        expired_entries = db.query(AnalysisCache).filter(
            AnalysisCache.expires_at < datetime.now()
        ).all()
        
        count = len(expired_entries)
        
        if count > 0:
            # Delete expired entries
            for entry in expired_entries:
                db.delete(entry)
            
            db.commit()
            logger.info(f"Deleted {count} expired cache entries")
        else:
            logger.debug("No expired cache entries found")
        
        return count
    
    def clear_all(
        self,
        db: Session
    ) -> int:
        """
        Clear all cache entries (use with caution)
        
        Args:
            db: Database session
            
        Returns:
            Number of entries deleted
        """
        logger.warning("Clearing all cache entries")
        
        count = db.query(AnalysisCache).count()
        db.query(AnalysisCache).delete()
        db.commit()
        
        logger.info(f"Cleared {count} cache entries")
        return count
    
    def get_cache_stats(
        self,
        db: Session
    ) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with cache statistics
        """
        total_entries = db.query(AnalysisCache).count()
        
        expired_entries = db.query(AnalysisCache).filter(
            AnalysisCache.expires_at < datetime.now()
        ).count()
        
        active_entries = total_entries - expired_entries
        
        # Get oldest and newest entries
        oldest = db.query(AnalysisCache).order_by(
            AnalysisCache.created_at.asc()
        ).first()
        
        newest = db.query(AnalysisCache).order_by(
            AnalysisCache.created_at.desc()
        ).first()
        
        stats = {
            "total_entries": total_entries,
            "active_entries": active_entries,
            "expired_entries": expired_entries,
            "oldest_entry": oldest.created_at if oldest else None,
            "newest_entry": newest.created_at if newest else None
        }
        
        logger.debug(f"Cache stats: {stats}")
        return stats


# Convenience functions for common cache keys

def make_trend_cache_key(days: int = 7) -> str:
    """
    Generate cache key for trend aggregation
    
    Args:
        days: Number of days analyzed
        
    Returns:
        Cache key string
    """
    # Include date to ensure daily refresh
    date_str = datetime.now().strftime("%Y-%m-%d")
    return f"trend_aggregation_{days}d_{date_str}"


def make_recommendation_cache_key(days: int = 7) -> str:
    """
    Generate cache key for recommendation
    
    Args:
        days: Number of days analyzed
        
    Returns:
        Cache key string
    """
    # Include date and hour to ensure hourly refresh
    datetime_str = datetime.now().strftime("%Y-%m-%d_%H")
    return f"recommendation_{days}d_{datetime_str}"


def make_analysis_cache_key(asset_type: str = "general", days: int = 7) -> str:
    """
    Generate cache key for complete analysis
    
    Args:
        asset_type: Type of asset analyzed
        days: Number of days analyzed
        
    Returns:
        Cache key string
    """
    datetime_str = datetime.now().strftime("%Y-%m-%d_%H")
    return f"analysis_{asset_type}_{days}d_{datetime_str}"
