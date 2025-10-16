"""
News Collection API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.database import get_db
from services.news_fetcher import NewsAPIClient
from services.sentiment_analyzer import SentimentAnalyzer
from models.news_article import NewsArticle, NewsArticleCreate
from models.sentiment_analysis import SentimentAnalysis, SentimentAnalysisCreate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/news", tags=["news"])

# Store for streaming logs
news_collection_logs = []
executor = ThreadPoolExecutor(max_workers=1)


def add_log(message: str, level: str = "info"):
    """Add a log message to the collection logs"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "message": message
    }
    news_collection_logs.append(log_entry)
    
    # Keep only last 1000 logs
    if len(news_collection_logs) > 1000:
        news_collection_logs.pop(0)
    
    # Also log to standard logger
    if level == "error":
        logger.error(message)
    elif level == "warning":
        logger.warning(message)
    else:
        logger.info(message)


def collect_news_task(
    days: int,
    query: str,
    language: str,
    db: Session
):
    """Background task for collecting news"""
    try:
        add_log(f"Starting news collection for last {days} days")
        
        # 1. Fetch news
        news_client = NewsAPIClient()
        from_date = datetime.now() - timedelta(days=days)
        to_date = datetime.now()
        
        add_log(f"Fetching news from {from_date.date()} to {to_date.date()}")
        add_log(f"Search query: {query}")
        
        articles = news_client.fetch_news(
            query=query,
            from_date=from_date,
            to_date=to_date,
            language=language,
            page_size=100
        )
        
        add_log(f"Fetched {len(articles)} articles from News API")
        
        if not articles:
            add_log("No articles fetched. Check your NEWS_API_KEY", "warning")
            return {
                "status": "warning",
                "message": "No articles fetched",
                "saved": 0,
                "analyzed": 0
            }
        
        # 2. Save to database
        saved_count = 0
        duplicate_count = 0
        
        for i, article_create in enumerate(articles):
            try:
                # Check for duplicates
                existing = db.query(NewsArticle).filter(
                    NewsArticle.url == article_create.url
                ).first()
                
                if existing:
                    duplicate_count += 1
                    continue
                
                # Save new article
                article = NewsArticle(**article_create.model_dump())
                db.add(article)
                saved_count += 1
                
                if (i + 1) % 10 == 0:
                    add_log(f"Processed {i + 1}/{len(articles)} articles...")
                
            except Exception as e:
                add_log(f"Failed to save article: {str(e)}", "error")
                continue
        
        db.commit()
        add_log(f"Saved {saved_count} new articles ({duplicate_count} duplicates skipped)")
        
        # 3. Sentiment analysis
        add_log("Starting sentiment analysis...")
        analyzer = SentimentAnalyzer()
        
        # Get articles without sentiment
        articles_to_analyze = db.query(NewsArticle).outerjoin(
            SentimentAnalysis,
            NewsArticle.id == SentimentAnalysis.article_id
        ).filter(
            SentimentAnalysis.id == None,
            NewsArticle.published_date >= from_date
        ).all()
        
        add_log(f"Found {len(articles_to_analyze)} articles to analyze")
        
        analyzed_count = 0
        for i, article in enumerate(articles_to_analyze):
            try:
                result = analyzer.analyze_article(article)
                
                sentiment_create = SentimentAnalysisCreate(
                    article_id=article.id,
                    sentiment=result.sentiment,
                    score=result.score,
                    reasoning=result.reasoning
                )
                
                sentiment = SentimentAnalysis(**sentiment_create.model_dump())
                db.add(sentiment)
                analyzed_count += 1
                
                if (i + 1) % 10 == 0:
                    add_log(f"Analyzed {i + 1}/{len(articles_to_analyze)} articles...")
                    db.commit()
                
            except Exception as e:
                add_log(f"Failed to analyze article {article.id}: {str(e)}", "error")
                continue
        
        db.commit()
        analyzer.close()
        
        add_log(f"Sentiment analysis completed: {analyzed_count} articles analyzed")
        
        # 4. Summary
        total_articles = db.query(NewsArticle).count()
        total_sentiments = db.query(SentimentAnalysis).count()
        
        add_log("=" * 60)
        add_log("Collection Summary:")
        add_log(f"  - Total articles in DB: {total_articles}")
        add_log(f"  - Total sentiments in DB: {total_sentiments}")
        add_log(f"  - New articles saved: {saved_count}")
        add_log(f"  - New sentiments analyzed: {analyzed_count}")
        add_log("=" * 60)
        
        return {
            "status": "success",
            "message": "News collection completed",
            "saved": saved_count,
            "analyzed": analyzed_count,
            "total_articles": total_articles,
            "total_sentiments": total_sentiments
        }
        
    except Exception as e:
        add_log(f"Error during news collection: {str(e)}", "error")
        db.rollback()
        return {
            "status": "error",
            "message": str(e)
        }


@router.post("/collect")
async def collect_news(
    days: int = Query(7, description="Number of days to collect news for"),
    query: str = Query("finance OR stock OR market OR economy", description="Search query"),
    language: str = Query("en", description="Language code"),
    db: Session = Depends(get_db)
):
    """
    Start news collection process
    
    - **days**: Number of days to collect news for (default: 7)
    - **query**: Search query for news
    - **language**: Language code (default: en)
    """
    try:
        # Clear previous logs
        news_collection_logs.clear()
        
        # Run collection in background
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor,
            collect_news_task,
            days,
            query,
            language,
            db
        )
        
        return result
        
    except Exception as e:
        add_log(f"Error starting news collection: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs")
async def get_collection_logs(
    limit: int = Query(100, description="Maximum number of logs to return")
):
    """
    Get news collection logs
    
    - **limit**: Maximum number of logs to return (default: 100)
    """
    return {
        "logs": news_collection_logs[-limit:] if news_collection_logs else []
    }


@router.get("/articles")
async def get_news_articles(
    limit: int = Query(50, description="Maximum number of articles to return"),
    days: int = Query(7, description="Number of days to look back"),
    db: Session = Depends(get_db)
):
    """
    Get recent news articles
    
    - **limit**: Maximum number of articles to return
    - **days**: Number of days to look back
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        articles = db.query(NewsArticle).filter(
            NewsArticle.published_date >= cutoff_date
        ).order_by(
            NewsArticle.published_date.desc()
        ).limit(limit).all()
        
        return {
            "articles": [
                {
                    "id": article.id,
                    "title": article.title,
                    "source": article.source,
                    "author": article.author,
                    "url": article.url,
                    "published_date": article.published_date.isoformat() if article.published_date else None,
                    "description": article.description
                }
                for article in articles
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/articles/{article_id}/sentiment")
async def get_article_sentiment(
    article_id: int,
    db: Session = Depends(get_db)
):
    """
    Get sentiment analysis for a specific article
    
    - **article_id**: Article ID
    """
    try:
        sentiment = db.query(SentimentAnalysis).filter(
            SentimentAnalysis.article_id == article_id
        ).first()
        
        if not sentiment:
            raise HTTPException(status_code=404, detail="Sentiment not found")
        
        return {
            "article_id": sentiment.article_id,
            "sentiment": sentiment.sentiment,
            "score": sentiment.score,
            "reasoning": sentiment.reasoning,
            "analyzed_at": sentiment.analyzed_at.isoformat() if sentiment.analyzed_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_news_stats(
    days: int = Query(7, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get news collection statistics
    
    - **days**: Number of days to analyze
    """
    try:
        from sqlalchemy import func
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Total articles
        total_articles = db.query(NewsArticle).filter(
            NewsArticle.published_date >= cutoff_date
        ).count()
        
        # Articles with sentiment
        articles_with_sentiment = db.query(NewsArticle).join(
            SentimentAnalysis,
            NewsArticle.id == SentimentAnalysis.article_id
        ).filter(
            NewsArticle.published_date >= cutoff_date
        ).count()
        
        # Sentiment distribution
        sentiment_dist = db.query(
            SentimentAnalysis.sentiment,
            func.count(SentimentAnalysis.id).label('count')
        ).join(
            NewsArticle,
            SentimentAnalysis.article_id == NewsArticle.id
        ).filter(
            NewsArticle.published_date >= cutoff_date
        ).group_by(
            SentimentAnalysis.sentiment
        ).all()
        
        return {
            "total_articles": total_articles,
            "articles_with_sentiment": articles_with_sentiment,
            "sentiment_distribution": {
                row.sentiment: row.count for row in sentiment_dist
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
