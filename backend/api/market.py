"""
Market Analysis API Endpoints

Provides endpoints for market sentiment analysis, news retrieval,
and daily sentiment data.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database import get_db
from models import NewsArticle, SentimentAnalysis
from config import settings
from services.trend_aggregator import TrendAggregator
from services.recommendation_engine import RecommendationEngine
from services.cache_service import CacheService

logger = logging.getLogger(__name__)

router = APIRouter()


# Response Models
class AnalyzeResponse(BaseModel):
    """Response model for /analyze endpoint"""
    buy_sell_ratio: int = Field(..., ge=0, le=100, description="Buy/sell ratio (0-100)")
    trend_summary: str = Field(..., description="Weekly trend summary")
    recommendation: str = Field(..., description="Investment recommendation")
    confidence: str = Field(..., description="Confidence level: low, medium, high")
    risk_assessment: str = Field(..., description="Risk assessment")
    key_considerations: List[str] = Field(default_factory=list, description="Key considerations")
    vix: float = Field(..., description="Current VIX value")
    signal_score: float = Field(..., description="Raw signal score")
    last_updated: datetime = Field(..., description="Timestamp of analysis")


class NewsArticleResponse(BaseModel):
    """Response model for news article"""
    id: int
    title: str
    content: str
    published_date: datetime
    source: str
    url: Optional[str] = None
    sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None
    
    class Config:
        from_attributes = True


class DailySentimentResponse(BaseModel):
    """Response model for daily sentiment data"""
    date: str
    average_score: float
    article_count: int
    positive_count: int
    negative_count: int
    neutral_count: int


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_market(
    asset_type: str = Query("general", description="Asset type to analyze"),
    db: Session = Depends(get_db)
):
    """
    Analyze market sentiment and generate buy/sell recommendation
    
    This endpoint performs the complete 3-step analysis:
    1. Aggregates weekly sentiment data
    2. Generates trend summary
    3. Produces conservative investment recommendation
    
    Results are cached for 1 hour to avoid redundant LLM calls.
    
    Args:
        asset_type: Type of asset to analyze (general, stock, crypto)
        db: Database session
        
    Returns:
        AnalyzeResponse with buy/sell ratio and detailed analysis
        
    Raises:
        HTTPException: If analysis fails or insufficient data
    """
    logger.info(f"Market analysis requested for asset_type: {asset_type}")
    
    try:
        # Check cache first
        cache_service = CacheService()
        cache_key = f"market_analysis_{asset_type}"
        
        cached_result = cache_service.get(db, cache_key)
        if cached_result:
            logger.info(f"Returning cached analysis for {asset_type}")
            return AnalyzeResponse(**cached_result)
        
        # Perform fresh analysis
        logger.info("Performing fresh market analysis")
        
        # Step 1 & 2: Aggregate weekly trend
        trend_aggregator = TrendAggregator()
        try:
            trend_summary = trend_aggregator.aggregate_weekly_trend(db, days=7)
        finally:
            trend_aggregator.close()
        
        # Step 3: Generate recommendation
        recommendation_engine = RecommendationEngine()
        try:
            recommendation = recommendation_engine.generate_recommendation(trend_summary)
        finally:
            recommendation_engine.close()
        
        # Build response
        response_data = {
            "buy_sell_ratio": recommendation.buy_sell_ratio,
            "trend_summary": recommendation.trend_summary,
            "recommendation": recommendation.recommendation,
            "confidence": recommendation.confidence,
            "risk_assessment": recommendation.risk_assessment,
            "key_considerations": recommendation.key_considerations,
            "vix": recommendation.vix,
            "signal_score": recommendation.signal_score,
            "last_updated": recommendation.last_updated.isoformat() if recommendation.last_updated else None
        }
        
        # Cache the result
        cache_service.set(
            db,
            cache_key,
            response_data,
            expiry_hours=settings.cache_expiry_hours
        )
        
        logger.info(
            f"Market analysis completed: ratio={recommendation.buy_sell_ratio}, "
            f"confidence={recommendation.confidence}"
        )
        
        return AnalyzeResponse(**response_data)
        
    except ValueError as e:
        logger.error(f"Insufficient data for analysis: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient data for analysis: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Market analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Market analysis failed: {str(e)}"
        )


@router.get("/news", response_model=List[NewsArticleResponse])
async def get_recent_news(
    days: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment: Positive, Negative, Neutral"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of articles to return"),
    db: Session = Depends(get_db)
):
    """
    Retrieve recent news articles with optional sentiment filter
    
    Args:
        days: Number of days to look back (1-30)
        sentiment: Optional sentiment filter
        limit: Maximum number of articles to return
        db: Database session
        
    Returns:
        List of news articles with sentiment data
        
    Raises:
        HTTPException: If query fails
    """
    logger.info(f"News retrieval requested: days={days}, sentiment={sentiment}, limit={limit}")
    
    try:
        # Calculate date range
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Query news articles
        query = db.query(NewsArticle).filter(
            NewsArticle.published_date >= cutoff_date
        )
        
        # Join with sentiment analysis
        articles = query.order_by(
            NewsArticle.published_date.desc()
        ).limit(limit).all()
        
        # Build response with sentiment data
        response = []
        for article in articles:
            # Get sentiment analysis if exists
            sentiment_analysis = db.query(SentimentAnalysis).filter(
                SentimentAnalysis.article_id == article.id
            ).first()
            
            # Filter by sentiment if specified
            if sentiment and sentiment_analysis:
                if sentiment_analysis.sentiment != sentiment:
                    continue
            
            article_data = {
                "id": article.id,
                "title": article.title,
                "content": article.content,
                "published_date": article.published_date,
                "source": article.source,
                "url": article.url,
                "sentiment": sentiment_analysis.sentiment if sentiment_analysis else None,
                "sentiment_score": sentiment_analysis.score if sentiment_analysis else None
            }
            response.append(NewsArticleResponse(**article_data))
        
        logger.info(f"Retrieved {len(response)} news articles")
        return response
        
    except Exception as e:
        logger.error(f"News retrieval failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve news: {str(e)}"
        )


@router.get("/sentiment/daily", response_model=List[DailySentimentResponse])
async def get_daily_sentiment(
    days: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    db: Session = Depends(get_db)
):
    """
    Retrieve daily aggregated sentiment scores
    
    Useful for charting sentiment trends over time.
    
    Args:
        days: Number of days to look back (1-30)
        db: Database session
        
    Returns:
        List of daily sentiment aggregates
        
    Raises:
        HTTPException: If query fails
    """
    logger.info(f"Daily sentiment data requested: days={days}")
    
    try:
        # Calculate date range
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Query sentiment analyses
        sentiments = db.query(SentimentAnalysis).filter(
            SentimentAnalysis.analyzed_at >= cutoff_date
        ).order_by(SentimentAnalysis.analyzed_at.asc()).all()
        
        if not sentiments:
            logger.warning("No sentiment data found for the specified period")
            return []
        
        # Group by date
        daily_data = {}
        for sentiment in sentiments:
            date_key = sentiment.analyzed_at.strftime("%Y-%m-%d")
            
            if date_key not in daily_data:
                daily_data[date_key] = {
                    "scores": [],
                    "positive": 0,
                    "negative": 0,
                    "neutral": 0
                }
            
            daily_data[date_key]["scores"].append(sentiment.score)
            
            if sentiment.sentiment == "Positive":
                daily_data[date_key]["positive"] += 1
            elif sentiment.sentiment == "Negative":
                daily_data[date_key]["negative"] += 1
            else:
                daily_data[date_key]["neutral"] += 1
        
        # Build response
        response = []
        for date_str, data in sorted(daily_data.items()):
            avg_score = sum(data["scores"]) / len(data["scores"])
            
            response.append(DailySentimentResponse(
                date=date_str,
                average_score=avg_score,
                article_count=len(data["scores"]),
                positive_count=data["positive"],
                negative_count=data["negative"],
                neutral_count=data["neutral"]
            ))
        
        logger.info(f"Retrieved daily sentiment data for {len(response)} days")
        return response
        
    except Exception as e:
        logger.error(f"Daily sentiment retrieval failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve daily sentiment: {str(e)}"
        )
