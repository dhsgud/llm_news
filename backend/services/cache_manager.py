"""
Cache Manager Service
Implements multi-tier caching strategy with Redis and database fallback
"""

import json
import logging
from typing import Optional, Any, Dict
from datetime import datetime, timedelta
from functools import wraps

try:
    import redis
    from redis.exceptions import RedisError, ConnectionError as RedisConnectionError
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from sqlalchemy.orm import Session

try:
    from config import settings
    from models.analysis_cache import AnalysisCache, AnalysisCacheCreate
except ImportError:
    from config import settings
    from models.analysis_cache import AnalysisCache, AnalysisCacheCreate


logger = logging.getLogger(__name__)


class CacheManager:
    """
    Multi-tier cache manager with Redis (L1) and Database (L2) caching
    
    Features:
    - Redis for fast in-memory caching (if enabled)
    - Database fallback for persistent caching
    - Automatic expiry management
    - Cache invalidation support
    """
    
    def __init__(self, db_session: Session):
        """
        Initialize cache manager
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session
        self.redis_client: Optional[redis.Redis] = None
        self.redis_enabled = False
        
        # Initialize Redis if enabled and available
        if settings.redis_enabled and REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(
                    settings.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # Test connection
                self.redis_client.ping()
                self.redis_enabled = True
                logger.info("Redis cache initialized successfully")
            except (RedisError, RedisConnectionError) as e:
                logger.warning(f"Redis connection failed, using database cache only: {e}")
                self.redis_client = None
                self.redis_enabled = False
        else:
            if not REDIS_AVAILABLE:
                logger.info("Redis library not available, using database cache only")
            else:
                logger.info("Redis disabled in settings, using database cache only")
    
    def _serialize_value(self, value: Any) -> str:
        """Serialize value to JSON string"""
        if isinstance(value, dict):
            return json.dumps(value)
        return json.dumps({"value": value})
    
    def _deserialize_value(self, value: str) -> Any:
        """Deserialize JSON string to value"""
        try:
            data = json.loads(value)
            if isinstance(data, dict) and "value" in data and len(data) == 1:
                return data["value"]
            return data
        except json.JSONDecodeError:
            return value
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache (Redis first, then database)
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        # Try Redis first (L1 cache)
        if self.redis_enabled and self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value is not None:
                    logger.debug(f"Cache hit (Redis): {key}")
                    return self._deserialize_value(value)
            except RedisError as e:
                logger.warning(f"Redis get error: {e}")
        
        # Fallback to database (L2 cache)
        try:
            cache_entry = self.db.query(AnalysisCache).filter(
                AnalysisCache.cache_key == key,
                AnalysisCache.expires_at > datetime.now()
            ).first()
            
            if cache_entry:
                logger.debug(f"Cache hit (Database): {key}")
                
                # Populate Redis if enabled
                if self.redis_enabled and self.redis_client:
                    try:
                        ttl = int((cache_entry.expires_at - datetime.now()).total_seconds())
                        if ttl > 0:
                            self.redis_client.setex(
                                key,
                                ttl,
                                self._serialize_value(cache_entry.result_json)
                            )
                    except RedisError as e:
                        logger.warning(f"Failed to populate Redis from database: {e}")
                
                return cache_entry.result_json
            
            logger.debug(f"Cache miss: {key}")
            return None
            
        except Exception as e:
            logger.error(f"Database cache get error: {e}")
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        ttl_hours: Optional[int] = None
    ) -> bool:
        """
        Set value in cache (both Redis and database)
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds
            ttl_hours: Time to live in hours (alternative to ttl_seconds)
            
        Returns:
            True if successful, False otherwise
        """
        # Calculate expiry time
        if ttl_seconds:
            expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        elif ttl_hours:
            expires_at = datetime.now() + timedelta(hours=ttl_hours)
        else:
            expires_at = datetime.now() + timedelta(hours=settings.cache_expiry_hours)
        
        ttl = int((expires_at - datetime.now()).total_seconds())
        
        # Ensure value is JSON serializable
        if not isinstance(value, dict):
            value = {"value": value}
        
        success = True
        
        # Set in Redis (L1 cache)
        if self.redis_enabled and self.redis_client:
            try:
                self.redis_client.setex(
                    key,
                    ttl,
                    self._serialize_value(value)
                )
                logger.debug(f"Cache set (Redis): {key}, TTL: {ttl}s")
            except RedisError as e:
                logger.warning(f"Redis set error: {e}")
                success = False
        
        # Set in database (L2 cache)
        try:
            # Check if entry exists
            existing = self.db.query(AnalysisCache).filter(
                AnalysisCache.cache_key == key
            ).first()
            
            if existing:
                # Update existing entry
                existing.result_json = value
                existing.expires_at = expires_at
                existing.created_at = datetime.now()
            else:
                # Create new entry
                cache_entry = AnalysisCache(
                    cache_key=key,
                    result_json=value,
                    expires_at=expires_at
                )
                self.db.add(cache_entry)
            
            self.db.commit()
            logger.debug(f"Cache set (Database): {key}, expires: {expires_at}")
            
        except Exception as e:
            logger.error(f"Database cache set error: {e}")
            self.db.rollback()
            success = False
        
        return success
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache (both Redis and database)
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        success = True
        
        # Delete from Redis
        if self.redis_enabled and self.redis_client:
            try:
                self.redis_client.delete(key)
                logger.debug(f"Cache deleted (Redis): {key}")
            except RedisError as e:
                logger.warning(f"Redis delete error: {e}")
                success = False
        
        # Delete from database
        try:
            self.db.query(AnalysisCache).filter(
                AnalysisCache.cache_key == key
            ).delete()
            self.db.commit()
            logger.debug(f"Cache deleted (Database): {key}")
        except Exception as e:
            logger.error(f"Database cache delete error: {e}")
            self.db.rollback()
            success = False
        
        return success
    
    def clear_expired(self) -> int:
        """
        Clear expired entries from database cache
        
        Returns:
            Number of entries deleted
        """
        try:
            count = self.db.query(AnalysisCache).filter(
                AnalysisCache.expires_at <= datetime.now()
            ).delete()
            self.db.commit()
            logger.info(f"Cleared {count} expired cache entries")
            return count
        except Exception as e:
            logger.error(f"Failed to clear expired cache: {e}")
            self.db.rollback()
            return 0
    
    def clear_all(self, pattern: Optional[str] = None) -> bool:
        """
        Clear all cache entries or entries matching pattern
        
        Args:
            pattern: Optional pattern to match keys (e.g., "analysis:*")
            
        Returns:
            True if successful, False otherwise
        """
        success = True
        
        # Clear Redis
        if self.redis_enabled and self.redis_client:
            try:
                if pattern:
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        self.redis_client.delete(*keys)
                        logger.info(f"Cleared {len(keys)} Redis keys matching '{pattern}'")
                else:
                    self.redis_client.flushdb()
                    logger.info("Cleared all Redis cache")
            except RedisError as e:
                logger.warning(f"Redis clear error: {e}")
                success = False
        
        # Clear database
        try:
            if pattern:
                # Convert Redis pattern to SQL LIKE pattern
                sql_pattern = pattern.replace('*', '%')
                count = self.db.query(AnalysisCache).filter(
                    AnalysisCache.cache_key.like(sql_pattern)
                ).delete(synchronize_session=False)
                logger.info(f"Cleared {count} database cache entries matching '{pattern}'")
            else:
                count = self.db.query(AnalysisCache).delete()
                logger.info(f"Cleared all {count} database cache entries")
            
            self.db.commit()
        except Exception as e:
            logger.error(f"Database cache clear error: {e}")
            self.db.rollback()
            success = False
        
        return success
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        stats = {
            "redis_enabled": self.redis_enabled,
            "redis_connected": False,
            "redis_keys": 0,
            "database_entries": 0,
            "database_expired": 0
        }
        
        # Redis stats
        if self.redis_enabled and self.redis_client:
            try:
                self.redis_client.ping()
                stats["redis_connected"] = True
                stats["redis_keys"] = self.redis_client.dbsize()
            except RedisError:
                pass
        
        # Database stats
        try:
            stats["database_entries"] = self.db.query(AnalysisCache).count()
            stats["database_expired"] = self.db.query(AnalysisCache).filter(
                AnalysisCache.expires_at <= datetime.now()
            ).count()
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
        
        return stats


def cached(
    key_prefix: str,
    ttl_seconds: Optional[int] = None,
    ttl_hours: Optional[int] = None
):
    """
    Decorator for caching function results
    
    Args:
        key_prefix: Prefix for cache key
        ttl_seconds: Time to live in seconds
        ttl_hours: Time to live in hours
        
    Example:
        @cached("stock_price", ttl_seconds=60)
        def get_stock_price(symbol: str):
            return fetch_price(symbol)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function arguments
            key_parts = [key_prefix]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            # Note: This requires db_session to be passed as first argument
            if args and hasattr(args[0], 'query'):
                db_session = args[0]
                cache_manager = CacheManager(db_session)
                
                cached_value = cache_manager.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                cache_manager.set(cache_key, result, ttl_seconds=ttl_seconds, ttl_hours=ttl_hours)
                return result
            else:
                # No db_session available, execute without caching
                return func(*args, **kwargs)
        
        return wrapper
    return decorator
