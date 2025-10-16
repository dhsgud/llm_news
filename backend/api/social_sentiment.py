"""
Social Sentiment API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

try:
    from app.database import get_db
    from models.social_models import (
        SocialPostResponse, SocialSentimentResponse,
        AggregatedSocialSentimentResponse, SocialSentimentSummary
    )
    from services.social_data_collector import SocialDataCollector
    from services.social_sentiment_analyzer import SocialSentimentAnalyzer
    from services.llm_client import LlamaCppClient
    from config import settings
except ImportError:
    from app.database import get_db
    from models.social_models import (
        SocialPostResponse, SocialSentimentResponse,
        AggregatedSocialSentimentResponse, SocialSentimentSummary
    )
    from services.social_data_collector import SocialDataCollector
    from services.social_sentiment_analyzer import SocialSentimentAnalyzer
    from services.llm_client import LlamaCppClient
    from config import settings


router = APIRouter(prefix="/api/social", tags=["social_sentiment"])


@router.post("/collect")
async def collect_social_data(
    symbols: Optional[List[str]] = Query(None, description="Stock symbols to search for"),
    db: Session = Depends(get_db)
):
    """
    Collect social media posts from Twitter and Reddit
    
    - **symbols**: Optional list of stock symbols to search for (e.g., ["AAPL", "TSLA"])
    """
    try:
        collector = SocialDataCollector(db)
        stats = collector.collect_all(symbols=symbols)
        
        return {
            "status": "success",
            "message": f"Collected {stats['total']} posts",
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error collecting social data: {str(e)}")


@router.post("/analyze")
async def analyze_social_sentiment(
    limit: int = Query(100, description="Maximum number of posts to analyze"),
    db: Session = Depends(get_db)
):
    """
    Analyze sentiment of unanalyzed social media posts
    
    - **limit**: Maximum number of posts to analyze in this batch
    """
    try:
        llm_client = LlamaCppClient(
            base_url=settings.LLAMA_CPP_URL,
            timeout=settings.LLAMA_CPP_TIMEOUT
        )
        analyzer = SocialSentimentAnalyzer(db, llm_client)
        
        # Get unanalyzed posts
        posts = analyzer.get_unanalyzed_posts(limit=limit)
        
        if not posts:
            return {
                "status": "success",
                "message": "No unanalyzed posts found",
                "analyzed_count": 0
            }
        
        # Analyze posts
        analyzed_count = analyzer.analyze_batch(posts)
        
        return {
            "status": "success",
            "message": f"Analyzed {analyzed_count} posts",
            "analyzed_count": analyzed_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing sentiment: {str(e)}")


@router.get("/sentiment/summary", response_model=List[SocialSentimentSummary])
async def get_sentiment_summary(
    symbol: Optional[str] = Query(None, description="Stock symbol (None for overall market)"),
    days: int = Query(7, description="Number of days to aggregate"),
    db: Session = Depends(get_db)
):
    """
    Get aggregated sentiment summary for a symbol or overall market
    
    - **symbol**: Stock symbol (e.g., "AAPL") or None for overall market
    - **days**: Number of days to aggregate (default: 7)
    """
    try:
        llm_client = LlamaCppClient(
            base_url=settings.LLAMA_CPP_URL,
            timeout=settings.LLAMA_CPP_TIMEOUT
        )
        analyzer = SocialSentimentAnalyzer(db, llm_client)
        
        summaries = analyzer.get_sentiment_summary(symbol=symbol, days=days)
        
        return summaries
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting sentiment summary: {str(e)}")


@router.get("/posts", response_model=List[SocialPostResponse])
async def get_social_posts(
    symbol: Optional[str] = Query(None, description="Filter by stock symbol"),
    platform: Optional[str] = Query(None, description="Filter by platform (twitter/reddit)"),
    limit: int = Query(50, description="Maximum number of posts to return"),
    db: Session = Depends(get_db)
):
    """
    Get social media posts
    
    - **symbol**: Filter by stock symbol
    - **platform**: Filter by platform (twitter or reddit)
    - **limit**: Maximum number of posts to return
    """
    try:
        from models.social_models import SocialPost
        
        query = db.query(SocialPost)
        
        if symbol:
            query = query.filter(SocialPost.symbol == symbol)
        
        if platform:
            query = query.filter(SocialPost.platform == platform)
        
        posts = query.order_by(SocialPost.created_at.desc()).limit(limit).all()
        
        return posts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting posts: {str(e)}")


@router.post("/aggregate")
async def aggregate_sentiment(
    symbol: Optional[str] = Query(None, description="Stock symbol to aggregate"),
    db: Session = Depends(get_db)
):
    """
    Aggregate and save sentiment data for a symbol
    
    - **symbol**: Stock symbol (None for overall market)
    """
    try:
        llm_client = LlamaCppClient(
            base_url=settings.LLAMA_CPP_URL,
            timeout=settings.LLAMA_CPP_TIMEOUT
        )
        analyzer = SocialSentimentAnalyzer(db, llm_client)
        
        analyzer.save_aggregated_sentiment(symbol=symbol)
        
        return {
            "status": "success",
            "message": f"Aggregated sentiment for {symbol or 'market'}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error aggregating sentiment: {str(e)}")


@router.delete("/cleanup")
async def cleanup_old_posts(
    days: int = Query(7, description="Delete posts older than this many days"),
    db: Session = Depends(get_db)
):
    """
    Delete old social media posts
    
    - **days**: Delete posts older than this many days (default: 7)
    """
    try:
        collector = SocialDataCollector(db)
        deleted = collector.cleanup_old_posts(days=days)
        
        return {
            "status": "success",
            "message": f"Deleted {deleted} old posts",
            "deleted_count": deleted
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cleaning up posts: {str(e)}")


@router.get("/trending")
async def get_trending_symbols(
    limit: int = Query(10, description="Number of trending symbols to return"),
    days: int = Query(1, description="Time period in days"),
    db: Session = Depends(get_db)
):
    """
    Get trending stock symbols based on social media activity
    
    - **limit**: Number of trending symbols to return
    - **days**: Time period to analyze (default: 1 day)
    """
    try:
        from models.social_models import SocialPost, SocialSentiment
        from sqlalchemy import func, desc
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get symbols with most posts and engagement
        trending = db.query(
            SocialPost.symbol,
            func.count(SocialPost.id).label('post_count'),
            func.sum(SocialPost.likes + SocialPost.shares + SocialPost.comments).label('engagement'),
            func.avg(SocialSentiment.score).label('avg_sentiment')
        ).join(
            SocialSentiment, SocialPost.id == SocialSentiment.post_id
        ).filter(
            SocialPost.symbol.isnot(None),
            SocialPost.created_at >= cutoff_date
        ).group_by(
            SocialPost.symbol
        ).order_by(
            desc('engagement')
        ).limit(limit).all()
        
        results = []
        for row in trending:
            results.append({
                'symbol': row.symbol,
                'post_count': row.post_count,
                'engagement': row.engagement,
                'avg_sentiment': float(row.avg_sentiment) if row.avg_sentiment else 0.0
            })
        
        return {
            "status": "success",
            "trending_symbols": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting trending symbols: {str(e)}")
