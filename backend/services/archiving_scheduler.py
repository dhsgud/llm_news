"""
Archiving Scheduler
Schedules automatic data archiving operations
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from typing import Optional

try:
    from app.database import SessionLocal
    from services.data_archiver import create_archiver
    from config import settings
except ImportError:
    from app.database import SessionLocal
    from services.data_archiver import create_archiver
    from config import settings

logger = logging.getLogger(__name__)


class ArchivingScheduler:
    """
    Scheduler for automatic data archiving operations
    Runs daily cleanup tasks to maintain database performance
    """
    
    def __init__(self):
        """Initialize the archiving scheduler"""
        self.scheduler = BackgroundScheduler()
        self.is_running = False
    
    def archive_old_data(self):
        """
        Scheduled task to archive old data
        Runs daily at 2:00 AM
        """
        logger.info("Starting scheduled data archiving...")
        db = SessionLocal()
        
        try:
            archiver = create_archiver(db)
            results = archiver.archive_all()
            
            total = sum(results.values())
            logger.info(f"Scheduled archiving completed. Total records archived: {total}")
            logger.info(f"Breakdown: {results}")
            
        except Exception as e:
            logger.error(f"Error during scheduled archiving: {str(e)}")
        finally:
            db.close()
    
    def clean_expired_cache(self):
        """
        Scheduled task to clean expired cache
        Runs every hour
        """
        logger.info("Starting scheduled cache cleanup...")
        db = SessionLocal()
        
        try:
            archiver = create_archiver(db)
            deleted = archiver.clean_expired_cache()
            
            logger.info(f"Scheduled cache cleanup completed. Deleted {deleted} entries")
            
        except Exception as e:
            logger.error(f"Error during scheduled cache cleanup: {str(e)}")
        finally:
            db.close()
    
    def start(self):
        """
        Start the archiving scheduler
        """
        if self.is_running:
            logger.warning("Archiving scheduler is already running")
            return
        
        try:
            # Schedule daily archiving at 2:00 AM
            self.scheduler.add_job(
                self.archive_old_data,
                trigger=CronTrigger(hour=2, minute=0),
                id='daily_archiving',
                name='Daily Data Archiving',
                replace_existing=True
            )
            logger.info("Scheduled daily archiving at 2:00 AM")
            
            # Schedule hourly cache cleanup
            self.scheduler.add_job(
                self.clean_expired_cache,
                trigger=CronTrigger(minute=0),
                id='hourly_cache_cleanup',
                name='Hourly Cache Cleanup',
                replace_existing=True
            )
            logger.info("Scheduled hourly cache cleanup")
            
            # Start the scheduler
            self.scheduler.start()
            self.is_running = True
            logger.info("Archiving scheduler started successfully")
            
        except Exception as e:
            logger.error(f"Error starting archiving scheduler: {str(e)}")
            raise
    
    def stop(self):
        """
        Stop the archiving scheduler
        """
        if not self.is_running:
            logger.warning("Archiving scheduler is not running")
            return
        
        try:
            self.scheduler.shutdown(wait=False)
            self.is_running = False
            logger.info("Archiving scheduler stopped")
            
        except Exception as e:
            logger.error(f"Error stopping archiving scheduler: {str(e)}")
            raise
    
    def run_now(self, task: str = 'all'):
        """
        Manually trigger archiving tasks
        
        Args:
            task: Task to run ('all', 'archive', 'cache')
        """
        if task in ['all', 'archive']:
            logger.info("Manually triggering data archiving...")
            self.archive_old_data()
        
        if task in ['all', 'cache']:
            logger.info("Manually triggering cache cleanup...")
            self.clean_expired_cache()


# Global scheduler instance
_scheduler: Optional[ArchivingScheduler] = None


def get_archiving_scheduler() -> ArchivingScheduler:
    """
    Get or create the global archiving scheduler instance
    
    Returns:
        ArchivingScheduler instance
    """
    global _scheduler
    if _scheduler is None:
        _scheduler = ArchivingScheduler()
    return _scheduler


def start_archiving_scheduler():
    """
    Start the global archiving scheduler
    """
    scheduler = get_archiving_scheduler()
    scheduler.start()


def stop_archiving_scheduler():
    """
    Stop the global archiving scheduler
    """
    scheduler = get_archiving_scheduler()
    scheduler.stop()
