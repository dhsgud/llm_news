#!/usr/bin/env python3
"""
뉴스 수집 스크립트
News API에서 뉴스를 가져와 데이터베이스에 저장하고 감성 분석을 수행합니다.
"""

import sys
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Add backend to path
sys.path.insert(0, '.')

from app.database import SessionLocal
from services.news_fetcher import NewsAPIClient
from services.sentiment_analyzer import SentimentAnalyzer
from models.news_article import NewsArticle, NewsArticleCreate
from models.sentiment_analysis import SentimentAnalysis, SentimentAnalysisCreate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def collect_and_analyze_news(
    days: int = 7,
    query: str = "finance OR stock OR market OR economy",
    language: str = "en"
):
    """
    뉴스를 수집하고 감성 분석을 수행합니다.
    
    Args:
        days: 수집할 일수 (기본 7일)
        query: 검색 쿼리
        language: 언어 코드
    """
    db = SessionLocal()
    
    try:
        logger.info(f"Starting news collection for last {days} days")
        
        # 1. 뉴스 수집
        news_client = NewsAPIClient()
        
        from_date = datetime.now() - timedelta(days=days)
        to_date = datetime.now()
        
        logger.info(f"Fetching news from {from_date.date()} to {to_date.date()}")
        articles = news_client.fetch_news(
            query=query,
            from_date=from_date,
            to_date=to_date,
            language=language,
            page_size=100
        )
        
        logger.info(f"Fetched {len(articles)} articles from News API")
        
        if not articles:
            logger.warning("No articles fetched. Check your NEWS_API_KEY in .env file")
            return
        
        # 2. 데이터베이스에 저장
        saved_count = 0
        duplicate_count = 0
        
        for article_create in articles:
            try:
                # article_create is already a NewsArticleCreate object
                # 중복 체크
                existing = db.query(NewsArticle).filter(
                    NewsArticle.url == article_create.url
                ).first()
                
                if existing:
                    duplicate_count += 1
                    continue
                
                # 새 기사 저장
                article = NewsArticle(**article_create.model_dump())
                db.add(article)
                saved_count += 1
                
            except Exception as e:
                logger.error(f"Failed to save article: {e}", exc_info=True)
                continue
        
        db.commit()
        logger.info(f"Saved {saved_count} new articles ({duplicate_count} duplicates skipped)")
        
        # 3. 감성 분석 수행
        logger.info("Starting sentiment analysis...")
        analyzer = SentimentAnalyzer()
        
        # 감성 분석이 없는 기사들 가져오기
        articles_to_analyze = db.query(NewsArticle).outerjoin(
            SentimentAnalysis,
            NewsArticle.id == SentimentAnalysis.article_id
        ).filter(
            SentimentAnalysis.id == None,
            NewsArticle.published_date >= from_date
        ).all()
        
        logger.info(f"Found {len(articles_to_analyze)} articles to analyze")
        
        analyzed_count = 0
        for article in articles_to_analyze:
            try:
                # 감성 분석 수행
                result = analyzer.analyze_article(article)
                
                # 결과 저장
                sentiment_create = SentimentAnalysisCreate(
                    article_id=article.id,
                    sentiment=result.sentiment,
                    score=result.score,
                    reasoning=result.reasoning
                )
                
                sentiment = SentimentAnalysis(**sentiment_create.model_dump())
                db.add(sentiment)
                analyzed_count += 1
                
                if analyzed_count % 10 == 0:
                    logger.info(f"Analyzed {analyzed_count}/{len(articles_to_analyze)} articles")
                    db.commit()
                
            except Exception as e:
                logger.error(f"Failed to analyze article {article.id}: {e}")
                continue
        
        db.commit()
        analyzer.close()
        
        logger.info(f"Sentiment analysis completed: {analyzed_count} articles analyzed")
        
        # 4. 결과 요약
        total_articles = db.query(NewsArticle).count()
        total_sentiments = db.query(SentimentAnalysis).count()
        
        logger.info("=" * 60)
        logger.info("Collection Summary:")
        logger.info(f"  - Total articles in DB: {total_articles}")
        logger.info(f"  - Total sentiments in DB: {total_sentiments}")
        logger.info(f"  - New articles saved: {saved_count}")
        logger.info(f"  - New sentiments analyzed: {analyzed_count}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error during news collection: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Collect and analyze news articles")
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to collect news for (default: 7)"
    )
    parser.add_argument(
        "--query",
        type=str,
        default="finance OR stock OR market OR economy",
        help="Search query for news"
    )
    parser.add_argument(
        "--language",
        type=str,
        default="en",
        help="Language code (default: en)"
    )
    
    args = parser.parse_args()
    
    collect_and_analyze_news(
        days=args.days,
        query=args.query,
        language=args.language
    )
