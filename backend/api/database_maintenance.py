"""
Database Maintenance API Endpoints
Provides endpoints for database optimization and archiving operations
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import logging

try:
    from app.database import get_db
    from services.data_archiver import DataArchiver, create_archiver
    from services.query_optimizer import QueryOptimizer, create_query_optimizer
except ImportError:
    from app.database import get_db
    from services.data_archiver import DataArchiver, create_archiver
    from services.query_optimizer import QueryOptimizer, create_query_optimizer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/maintenance", tags=["Database Maintenance"])


# Request/Response Models

class ArchiveRequest(BaseModel):
    """Request model for archiving operations"""
    retention_periods: Optional[Dict[str, int]] = Field(
        None,
        description="Custom retention periods in days for each table"
    )


class ArchiveResponse(BaseModel):
    """Response model for archiving operations"""
    success: bool
    message: str
    archived_counts: Dict[str, int]


class StatisticsResponse(BaseModel):
    """Response model for database statistics"""
    table_statistics: Dict[str, Dict[str, Any]]
    cache_statistics: Dict[str, Any]


class MaintenanceResponse(BaseModel):
    """Response model for maintenance operations"""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None


# Endpoints

@router.post("/archive", response_model=ArchiveResponse)
async def archive_old_data(
    request: ArchiveRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Archive old data based on retention policies
    
    This endpoint runs archiving operations in the background to avoid blocking.
    Default retention periods:
    - news_articles: 30 days
    - sentiment_analysis: 30 days
    - stock_prices: 90 days
    - trade_history: 365 days
    - analysis_cache: 7 days
    - stock_news_relation: 30 days
    """
    try:
        archiver = create_archiver(db, request.retention_periods)
        
        # Run archiving in background
        def run_archiving():
            try:
                results = archiver.archive_all()
                logger.info(f"Background archiving completed: {results}")
            except Exception as e:
                logger.error(f"Background archiving failed: {str(e)}")
        
        background_tasks.add_task(run_archiving)
        
        return ArchiveResponse(
            success=True,
            message="Archiving operation started in background",
            archived_counts={}
        )
        
    except Exception as e:
        logger.error(f"Error starting archiving operation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/archive/immediate", response_model=ArchiveResponse)
async def archive_old_data_immediate(
    request: ArchiveRequest,
    db: Session = Depends(get_db)
):
    """
    Archive old data immediately (synchronous operation)
    
    Use this endpoint for manual archiving operations.
    Warning: This may take some time depending on data volume.
    """
    try:
        archiver = create_archiver(db, request.retention_periods)
        results = archiver.archive_all()
        
        total = sum(results.values())
        
        return ArchiveResponse(
            success=True,
            message=f"Successfully archived {total} records",
            archived_counts=results
        )
        
    except Exception as e:
        logger.error(f"Error during archiving: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", response_model=StatisticsResponse)
async def get_database_statistics(db: Session = Depends(get_db)):
    """
    Get database statistics including table sizes and cache hit rates
    """
    try:
        archiver = create_archiver(db)
        optimizer = create_query_optimizer(db)
        
        table_stats = archiver.get_table_statistics()
        cache_stats = optimizer.get_cache_hit_rate()
        
        return StatisticsResponse(
            table_statistics=table_stats,
            cache_statistics=cache_stats
        )
        
    except Exception as e:
        logger.error(f"Error getting database statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clean-cache", response_model=MaintenanceResponse)
async def clean_expired_cache(db: Session = Depends(get_db)):
    """
    Clean expired cache entries
    """
    try:
        archiver = create_archiver(db)
        deleted = archiver.clean_expired_cache()
        
        return MaintenanceResponse(
            success=True,
            message=f"Cleaned {deleted} expired cache entries",
            details={"deleted_count": deleted}
        )
        
    except Exception as e:
        logger.error(f"Error cleaning cache: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize", response_model=MaintenanceResponse)
async def optimize_database(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Run database optimization (VACUUM ANALYZE for PostgreSQL)
    
    This operation runs in the background and updates table statistics
    for better query planning.
    """
    try:
        optimizer = create_query_optimizer(db)
        
        # Run optimization in background
        def run_optimization():
            try:
                optimizer.vacuum_analyze_tables()
                logger.info("Database optimization completed")
            except Exception as e:
                logger.error(f"Database optimization failed: {str(e)}")
        
        background_tasks.add_task(run_optimization)
        
        return MaintenanceResponse(
            success=True,
            message="Database optimization started in background"
        )
        
    except Exception as e:
        logger.error(f"Error starting optimization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/archive/news/{days}")
async def archive_news_by_days(
    days: int,
    db: Session = Depends(get_db)
):
    """
    Archive news articles older than specified days
    """
    try:
        archiver = create_archiver(db)
        deleted = archiver.archive_old_news(days)
        
        return MaintenanceResponse(
            success=True,
            message=f"Archived {deleted} news articles older than {days} days",
            details={"deleted_count": deleted, "retention_days": days}
        )
        
    except Exception as e:
        logger.error(f"Error archiving news: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/archive/stock-prices/{days}")
async def archive_stock_prices_by_days(
    days: int,
    db: Session = Depends(get_db)
):
    """
    Archive stock prices older than specified days
    """
    try:
        archiver = create_archiver(db)
        deleted = archiver.archive_old_stock_prices(days)
        
        return MaintenanceResponse(
            success=True,
            message=f"Archived {deleted} stock price records older than {days} days",
            details={"deleted_count": deleted, "retention_days": days}
        )
        
    except Exception as e:
        logger.error(f"Error archiving stock prices: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/archive/trades/{days}")
async def archive_trades_by_days(
    days: int,
    db: Session = Depends(get_db)
):
    """
    Archive trade history older than specified days
    """
    try:
        archiver = create_archiver(db)
        deleted = archiver.archive_old_trade_history(days)
        
        return MaintenanceResponse(
            success=True,
            message=f"Archived {deleted} trade records older than {days} days",
            details={"deleted_count": deleted, "retention_days": days}
        )
        
    except Exception as e:
        logger.error(f"Error archiving trades: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
