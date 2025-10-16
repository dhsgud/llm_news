"""
Example: Complete Trend Analysis and Recommendation Pipeline

This example demonstrates the full 3-step analysis workflow:
1. TrendAggregator: Aggregates 7 days of sentiment data
2. RecommendationEngine: Generates investment recommendation
3. CacheService: Caches results for 1 hour

Prerequisites:
- Database with sentiment analysis data
- llama.cpp server running on localhost:8080
- Apriel-1.5-15b-Thinker model loaded
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from models import Base
from services.trend_aggregator import TrendAggregator
from services.recommendation_engine import RecommendationEngine
from services.cache_service import CacheService, make_analysis_cache_key
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_complete_analysis(db: Session, use_cache: bool = True):
    """
    Run complete trend analysis and recommendation pipeline
    
    Args:
        db: Database session
        use_cache: Whether to use caching
    """
    logger.info("=" * 60)
    logger.info("Starting Complete Market Analysis Pipeline")
    logger.info("=" * 60)
    
    # Initialize services
    cache_service = CacheService()
    trend_aggregator = TrendAggregator()
    recommendation_engine = RecommendationEngine()
    
    try:
        # Check cache first
        cache_key = make_analysis_cache_key(asset_type="general", days=7)
        
        if use_cache:
            logger.info(f"\nChecking cache with key: {cache_key}")
            cached_result = cache_service.get(db, cache_key)
            
            if cached_result:
                logger.info("??Found cached result!")
                print("\n" + "=" * 60)
                print("CACHED ANALYSIS RESULT")
                print("=" * 60)
                print_analysis_result(cached_result)
                return cached_result
            else:
                logger.info("??No cached result found, running fresh analysis")
        
        # Step 1: Aggregate weekly trend
        logger.info("\n" + "-" * 60)
        logger.info("STEP 1: Aggregating Weekly Trend")
        logger.info("-" * 60)
        
        trend_summary = trend_aggregator.aggregate_weekly_trend(
            db=db,
            days=7,
            temperature=0.5,
            max_tokens=1000
        )
        
        logger.info(f"??Trend aggregation completed")
        logger.info(f"  Period: {trend_summary.period_start.date()} to {trend_summary.period_end.date()}")
        logger.info(f"  Articles analyzed: {trend_summary.total_articles}")
        logger.info(f"  Dominant sentiment: {trend_summary.dominant_sentiment}")
        logger.info(f"  Average score: {trend_summary.average_score:+.2f}")
        
        # Step 2: Generate recommendation
        logger.info("\n" + "-" * 60)
        logger.info("STEP 2: Generating Investment Recommendation")
        logger.info("-" * 60)
        
        recommendation = recommendation_engine.generate_recommendation(
            trend=trend_summary,
            temperature=0.7,
            max_tokens=1500
        )
        
        logger.info(f"??Recommendation generated")
        logger.info(f"  Buy/Sell Ratio: {recommendation.buy_sell_ratio}")
        logger.info(f"  Confidence: {recommendation.confidence}")
        logger.info(f"  VIX: {recommendation.vix:.2f}")
        
        # Prepare result for caching
        result = {
            "buy_sell_ratio": recommendation.buy_sell_ratio,
            "recommendation": recommendation.recommendation,
            "confidence": recommendation.confidence,
            "risk_assessment": recommendation.risk_assessment,
            "key_considerations": recommendation.key_considerations,
            "trend_summary": recommendation.trend_summary,
            "dominant_sentiment": trend_summary.dominant_sentiment,
            "key_drivers": trend_summary.key_drivers,
            "vix": recommendation.vix,
            "vix_normalized": recommendation.vix_normalized,
            "signal_score": recommendation.signal_score,
            "period_start": trend_summary.period_start.isoformat(),
            "period_end": trend_summary.period_end.isoformat(),
            "total_articles": trend_summary.total_articles,
            "average_score": trend_summary.average_score,
            "last_updated": recommendation.last_updated.isoformat()
        }
        
        # Cache the result
        if use_cache:
            logger.info("\n" + "-" * 60)
            logger.info("STEP 3: Caching Result")
            logger.info("-" * 60)
            
            cache_service.set(
                db=db,
                cache_key=cache_key,
                result=result,
                expiry_hours=1
            )
            
            logger.info(f"??Result cached with key: {cache_key}")
            logger.info(f"  Cache expires in: 1 hour")
        
        # Display final result
        print("\n" + "=" * 60)
        print("FINAL ANALYSIS RESULT")
        print("=" * 60)
        print_analysis_result(result)
        
        return result
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise
        
    finally:
        # Clean up
        trend_aggregator.close()
        recommendation_engine.close()


def print_analysis_result(result: dict):
    """
    Pretty print analysis result
    
    Args:
        result: Analysis result dictionary
    """
    print(f"\n?�� Market Analysis Report")
    print(f"Period: {result['period_start'][:10]} to {result['period_end'][:10]}")
    print(f"Last Updated: {result['last_updated'][:19]}")
    print(f"\n{'?�' * 60}")
    
    # Buy/Sell Ratio
    ratio = result['buy_sell_ratio']
    if ratio <= 30:
        indicator = "?�� STRONG SELL"
        color = "RED"
    elif ratio <= 70:
        indicator = "?�� NEUTRAL"
        color = "YELLOW"
    else:
        indicator = "?�� STRONG BUY"
        color = "GREEN"
    
    print(f"\n?�� Buy/Sell Ratio: {ratio}/100")
    print(f"   Signal: {indicator}")
    print(f"   Confidence: {result['confidence'].upper()}")
    
    # Market Sentiment
    print(f"\n?�� Market Sentiment")
    print(f"   Dominant: {result['dominant_sentiment']}")
    print(f"   Average Score: {result['average_score']:+.2f}")
    print(f"   Articles Analyzed: {result['total_articles']}")
    
    # VIX & Volatility
    print(f"\n?�� Market Volatility")
    print(f"   VIX: {result['vix']:.2f}")
    print(f"   Normalized VIX: {result['vix_normalized']:.3f}")
    print(f"   Signal Score: {result['signal_score']:+.2f}")
    
    # Trend Summary
    print(f"\n?�� Trend Summary")
    print(f"   {result['trend_summary']}")
    
    # Key Drivers
    if result.get('key_drivers'):
        print(f"\n?�� Key Market Drivers")
        for i, driver in enumerate(result['key_drivers'], 1):
            print(f"   {i}. {driver}")
    
    # Recommendation
    print(f"\n?�� Investment Recommendation")
    print(f"   {result['recommendation']}")
    
    # Risk Assessment
    print(f"\n?�️  Risk Assessment")
    print(f"   {result['risk_assessment']}")
    
    # Key Considerations
    if result.get('key_considerations'):
        print(f"\n?�� Key Considerations")
        for i, consideration in enumerate(result['key_considerations'], 1):
            print(f"   {i}. {consideration}")
    
    print(f"\n{'?�' * 60}\n")


def show_cache_stats(db: Session):
    """
    Display cache statistics
    
    Args:
        db: Database session
    """
    cache_service = CacheService()
    stats = cache_service.get_cache_stats(db)
    
    print("\n" + "=" * 60)
    print("CACHE STATISTICS")
    print("=" * 60)
    print(f"Total Entries: {stats['total_entries']}")
    print(f"Active Entries: {stats['active_entries']}")
    print(f"Expired Entries: {stats['expired_entries']}")
    
    if stats['oldest_entry']:
        print(f"Oldest Entry: {stats['oldest_entry']}")
    if stats['newest_entry']:
        print(f"Newest Entry: {stats['newest_entry']}")
    
    print("=" * 60 + "\n")


def cleanup_expired_cache(db: Session):
    """
    Clean up expired cache entries
    
    Args:
        db: Database session
    """
    cache_service = CacheService()
    deleted_count = cache_service.cleanup_expired(db)
    
    logger.info(f"Cleaned up {deleted_count} expired cache entries")


def main():
    """Main execution function"""
    # Create database session
    db = SessionLocal()
    
    try:
        # Show cache stats before
        show_cache_stats(db)
        
        # Run complete analysis
        result = run_complete_analysis(db, use_cache=True)
        
        # Show cache stats after
        show_cache_stats(db)
        
        # Clean up expired entries
        cleanup_expired_cache(db)
        
        logger.info("\n??Analysis pipeline completed successfully!")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise
        
    finally:
        db.close()


if __name__ == "__main__":
    main()
