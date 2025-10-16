"""
Cache Maintenance Scheduler
Periodically clears expired cache entries
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

try:
    from app.database import SessionLocal
    from services.cache_manager import CacheManager
except ImportError:
    from app.database import SessionLocal
    from services.cache_manager import CacheManager


logger = logging.getLogger(__name__)


class CacheScheduler:
    """
    Background scheduler for cache maintenance tasks
    """
    
    def __init__(self):
        """Initialize cache scheduler"""
        self.scheduler = BackgroundScheduler()
        self.is_running = False
    
    def clear_expired_cache(self):
        """
        Clear expired cache entries from database
        This task runs periodically to clean up old cache entries
        """
        try:
            db = SessionLocal()
            cache_manager = CacheManager(db)
            
            count = cache_manager.clear_expired()
            logger.info(f"Cache maintenance: Cleared {count} expired entries")
            
            db.close()
            
        except Exception as e:
            logger.error(f"Failed to clear expired cache: {e}")
    
    def start(self):
        """
        Start the cache maintenance scheduler
        Runs cache cleanup every hour
        """
        if self.is_running:
            logger.warning("Cache scheduler is already running")
            return
        
        try:
            # Schedule cache cleanup every hour
            self.scheduler.add_job(
                self.clear_expired_cache,
                trigger=IntervalTrigger(hours=1),
                id="clear_expired_cache",
                name="Clear expired cache entries",
                replace_existing=True
            )
            
            self.scheduler.start()
            self.is_running = True
            logger.info("Cache scheduler started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start cache scheduler: {e}")
            raise
    
    def stop(self):
        """Stop the cache maintenance scheduler"""
        if not self.is_running:
            logger.warning("Cache scheduler is not running")
            return
        
        try:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Cache scheduler stopped")
            
        except Exception as e:
            logger.error(f"Failed to stop cache scheduler: {e}")
            raise


# Global scheduler instance
_cache_scheduler = None


def get_cache_scheduler() -> CacheScheduler:
    """Get or create global cache scheduler instance"""
    global _cache_scheduler
    if _cache_scheduler is None:
        _cache_scheduler = CacheScheduler()
    return _cache_scheduler


def start_cache_scheduler():
    """Start the global cache scheduler"""
    scheduler = get_cache_scheduler()
    scheduler.start()


def stop_cache_scheduler():
    """Stop the global cache scheduler"""
    scheduler = get_cache_scheduler()
    scheduler.stop()
