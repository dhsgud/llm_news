#!/usr/bin/env python3
"""
Database migration script for news collection feature
Adds description and author fields to news_articles table
"""

import sys
import logging
from sqlalchemy import text

# Add backend to path
sys.path.insert(0, '.')

from app.database import engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_migration():
    """Run the migration to add new fields to news_articles table"""
    
    logger.info("Starting news collection migration...")
    
    try:
        with engine.connect() as conn:
            # Check if columns already exist
            result = conn.execute(text("""
                SELECT COUNT(*) as count
                FROM pragma_table_info('news_articles')
                WHERE name IN ('description', 'author')
            """))
            
            existing_columns = result.fetchone()[0]
            
            if existing_columns == 2:
                logger.info("Columns 'description' and 'author' already exist. Skipping migration.")
                return
            
            # Add description column if it doesn't exist
            if existing_columns < 2:
                logger.info("Adding 'description' column to news_articles table...")
                conn.execute(text("""
                    ALTER TABLE news_articles 
                    ADD COLUMN description TEXT
                """))
                conn.commit()
                logger.info("Added 'description' column successfully")
            
            # Add author column if it doesn't exist
            logger.info("Adding 'author' column to news_articles table...")
            conn.execute(text("""
                ALTER TABLE news_articles 
                ADD COLUMN author VARCHAR(200)
            """))
            conn.commit()
            logger.info("Added 'author' column successfully")
            
            logger.info("Migration completed successfully!")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    run_migration()
