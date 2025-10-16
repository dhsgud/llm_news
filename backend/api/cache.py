"""
Cache Management API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging

try:
    from app.database import get_db
    from services.cache_manager import CacheManager
    from services.stock_price_cache import StockPriceCache
    from services.analysis_cache_service import AnalysisCacheService
except ImportError:
    from app.database import get_db
    from services.cache_manager import CacheManager
    from services.stock_price_cache import StockPriceCache
    from services.analysis_cache_service import AnalysisCacheService


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/cache/stats")
async def get_cache_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get cache statistics
    
    Returns overall cache health and usage statistics
    """
    try:
        cache_manager = CacheManager(db)
        stock_cache = StockPriceCache(db)
        analysis_cache = AnalysisCacheService(db)
        
        overall_stats = cache_manager.get_stats()
        
        return {
            "status": "healthy",
            "overall": overall_stats,
            "stock_price_cache": {
                "ttl_seconds": stock_cache.CACHE_TTL_SECONDS
            },
            "analysis_cache": {
                "ttl_hours": analysis_cache.CACHE_TTL_HOURS
            }
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")


@router.post("/cache/clear")
async def clear_cache(
    cache_type: Optional[str] = Query(
        None,
        description="Type of cache to clear: 'all', 'analysis', 'stock_price', or None for expired only"
    ),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Clear cache entries
    
    Args:
        cache_type: Type of cache to clear
            - 'all': Clear all caches
            - 'analysis': Clear analysis caches only
            - 'stock_price': Clear stock price caches only
            - None: Clear expired entries only
    
    Returns:
        Status message
    """
    try:
        cache_manager = CacheManager(db)
        
        if cache_type == "all":
            success = cache_manager.clear_all()
            message = "All caches cleared"
        elif cache_type == "analysis":
            analysis_cache = AnalysisCacheService(db)
            success = analysis_cache.invalidate_all_analysis()
            message = "Analysis caches cleared"
        elif cache_type == "stock_price":
            stock_cache = StockPriceCache(db)
            success = stock_cache.clear_all_prices()
            message = "Stock price caches cleared"
        elif cache_type is None:
            count = cache_manager.clear_expired()
            success = True
            message = f"Cleared {count} expired cache entries"
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid cache_type: {cache_type}. Must be 'all', 'analysis', 'stock_price', or None"
            )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to clear cache")
        
        logger.info(message)
        return {
            "status": "success",
            "message": message,
            "cache_type": cache_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@router.delete("/cache/analysis/{asset_type}")
async def invalidate_market_analysis(
    asset_type: str,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Invalidate market analysis cache for specific asset type
    
    Args:
        asset_type: Asset type (e.g., 'general', 'stock', 'crypto')
    
    Returns:
        Status message
    """
    try:
        analysis_cache = AnalysisCacheService(db)
        success = analysis_cache.invalidate_market_analysis(asset_type)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to invalidate cache")
        
        logger.info(f"Invalidated market analysis cache: {asset_type}")
        return {
            "status": "success",
            "message": f"Market analysis cache invalidated for {asset_type}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to invalidate market analysis cache: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to invalidate cache: {str(e)}"
        )


@router.delete("/cache/stock/{symbol}")
async def invalidate_stock_cache(
    symbol: str,
    cache_type: str = Query(
        "all",
        description="Type of cache to invalidate: 'all', 'price', or 'sentiment'"
    ),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Invalidate cache for specific stock
    
    Args:
        symbol: Stock symbol
        cache_type: Type of cache to invalidate
    
    Returns:
        Status message
    """
    try:
        symbol = symbol.upper()
        
        if cache_type in ["all", "price"]:
            stock_cache = StockPriceCache(db)
            stock_cache.invalidate_price(symbol)
        
        if cache_type in ["all", "sentiment"]:
            analysis_cache = AnalysisCacheService(db)
            analysis_cache.invalidate_stock_sentiment(symbol)
        
        logger.info(f"Invalidated {cache_type} cache for stock: {symbol}")
        return {
            "status": "success",
            "message": f"Cache invalidated for {symbol} ({cache_type})"
        }
        
    except Exception as e:
        logger.error(f"Failed to invalidate stock cache: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to invalidate cache: {str(e)}"
        )


@router.post("/cache/warmup")
async def warmup_cache(
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Warm up cache by pre-loading common data
    
    This endpoint can be called after deployment or cache clear
    to pre-populate frequently accessed data
    
    Returns:
        Status message
    """
    try:
        # This is a placeholder for cache warmup logic
        # In a real implementation, you would:
        # 1. Load most frequently accessed stocks
        # 2. Pre-compute market analysis
        # 3. Cache common queries
        
        logger.info("Cache warmup initiated")
        return {
            "status": "success",
            "message": "Cache warmup completed"
        }
        
    except Exception as e:
        logger.error(f"Failed to warm up cache: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to warm up cache: {str(e)}"
        )
