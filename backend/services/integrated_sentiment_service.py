"""
Integrated Sentiment Service
Combines news sentiment and social sentiment for comprehensive analysis
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

try:
    from models.sentiment_analysis import SentimentAnalysis
    from models.social_models import SocialPost, SocialSentiment
    from services.social_sentiment_analyzer import SocialSentimentAnalyzer
    from services.llm_client import LlamaCppClient
except ImportError:
    from models.sentiment_analysis import SentimentAnalysis
    from models.social_models import SocialPost, SocialSentiment
    from services.social_sentiment_analyzer import SocialSentimentAnalyzer
    from services.llm_client import LlamaCppClient


logger = logging.getLogger(__name__)


class IntegratedSentimentService:
    """Combines news and social sentiment for comprehensive market analysis"""
    
    def __init__(self, db: Session, llm_client: LlamaCppClient):
        self.db = db
        self.llm_client = llm_client
        self.social_analyzer = SocialSentimentAnalyzer(db, llm_client)
    
    def get_combined_sentiment(self, symbol: Optional[str] = None, days: int = 7) -> Dict:
        """
        Get combined sentiment from news and social media
        
        Args:
            symbol: Stock symbol (None for overall market)
            days: Number of days to analyze
        
        Returns:
            Dictionary with combined sentiment analysis
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get news sentiment
        news_query = self.db.query(
            func.count(SentimentAnalysis.id).label('count'),
            func.avg(SentimentAnalysis.score).label('avg_score'),
            func.sum(func.case((SentimentAnalysis.sentiment == 'Positive', 1), else_=0)).label('positive'),
            func.sum(func.case((SentimentAnalysis.sentiment == 'Negative', 1), else_=0)).label('negative'),
            func.sum(func.case((SentimentAnalysis.sentiment == 'Neutral', 1), else_=0)).label('neutral')
        ).filter(SentimentAnalysis.analyzed_at >= cutoff_date)
        
        if symbol:
            # Join with news articles to filter by symbol
            from models.news_article import NewsArticle
            news_query = news_query.join(
                NewsArticle, SentimentAnalysis.article_id == NewsArticle.id
            ).filter(NewsArticle.title.contains(symbol))
        
        news_result = news_query.first()
        
        # Get social sentiment
        social_aggregated = self.social_analyzer.aggregate_sentiment(symbol=symbol, days=days)
        
        # Combine results
        combined = {
            'symbol': symbol,
            'period_days': days,
            'news_sentiment': {
                'count': news_result.count or 0,
                'avg_score': float(news_result.avg_score) if news_result.avg_score else 0.0,
                'positive': news_result.positive or 0,
                'negative': news_result.negative or 0,
                'neutral': news_result.neutral or 0
            },
            'social_sentiment': social_aggregated,
            'combined_score': self._calculate_combined_score(
                news_result.avg_score or 0.0,
                news_result.count or 0,
                social_aggregated
            )
        }
        
        return combined
    
    def _calculate_combined_score(
        self,
        news_avg: float,
        news_count: int,
        social_data: Dict
    ) -> float:
        """
        Calculate weighted combined sentiment score
        
        Weights:
        - News: 60% (more reliable, fact-based)
        - Social: 40% (real-time, sentiment-driven)
        """
        if news_count == 0 and not social_data:
            return 0.0
        
        news_weight = 0.6
        social_weight = 0.4
        
        # Calculate weighted news score
        news_score = news_avg * news_weight if news_count > 0 else 0.0
        
        # Calculate weighted social score (average across platforms)
        social_scores = []
        for platform_data in social_data.values():
            if platform_data['post_count'] > 0:
                social_scores.append(platform_data['avg_sentiment'])
        
        social_avg = sum(social_scores) / len(social_scores) if social_scores else 0.0
        social_score = social_avg * social_weight
        
        # Combined score
        combined = news_score + social_score
        
        return round(combined, 3)
    
    def get_sentiment_divergence(self, symbol: Optional[str] = None, days: int = 7) -> Dict:
        """
        Detect divergence between news and social sentiment
        Large divergence may indicate market inefficiency or manipulation
        
        Returns:
            Dictionary with divergence analysis
        """
        combined = self.get_combined_sentiment(symbol=symbol, days=days)
        
        news_score = combined['news_sentiment']['avg_score']
        
        # Average social score across platforms
        social_scores = []
        for platform_data in combined['social_sentiment'].values():
            if platform_data['post_count'] > 0:
                social_scores.append(platform_data['avg_sentiment'])
        
        social_score = sum(social_scores) / len(social_scores) if social_scores else 0.0
        
        # Calculate divergence
        divergence = abs(news_score - social_score)
        
        # Interpret divergence
        if divergence < 0.3:
            interpretation = "Aligned - News and social sentiment agree"
        elif divergence < 0.7:
            interpretation = "Moderate divergence - Some disagreement"
        else:
            interpretation = "High divergence - Significant disagreement, investigate further"
        
        return {
            'symbol': symbol,
            'news_score': news_score,
            'social_score': social_score,
            'divergence': round(divergence, 3),
            'interpretation': interpretation,
            'recommendation': self._get_divergence_recommendation(news_score, social_score, divergence)
        }
    
    def _get_divergence_recommendation(self, news_score: float, social_score: float, divergence: float) -> str:
        """Get trading recommendation based on sentiment divergence"""
        if divergence < 0.3:
            # Aligned sentiment
            if news_score > 0.5:
                return "Strong buy signal - Both news and social are positive"
            elif news_score < -0.5:
                return "Strong sell signal - Both news and social are negative"
            else:
                return "Hold - Neutral sentiment across sources"
        else:
            # Divergent sentiment
            if news_score > social_score:
                return "Cautious buy - News positive but social skeptical, wait for confirmation"
            else:
                return "Cautious sell - Social negative but news positive, monitor closely"
    
    def get_sentiment_trend(self, symbol: Optional[str] = None, days: int = 7) -> Dict:
        """
        Analyze sentiment trend over time
        
        Returns:
            Dictionary with daily sentiment scores
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get daily news sentiment
        from models.news_article import NewsArticle
        
        news_daily = self.db.query(
            func.date(SentimentAnalysis.analyzed_at).label('date'),
            func.avg(SentimentAnalysis.score).label('avg_score')
        ).filter(
            SentimentAnalysis.analyzed_at >= cutoff_date
        )
        
        if symbol:
            news_daily = news_daily.join(
                NewsArticle, SentimentAnalysis.article_id == NewsArticle.id
            ).filter(NewsArticle.title.contains(symbol))
        
        news_daily = news_daily.group_by(func.date(SentimentAnalysis.analyzed_at)).all()
        
        # Get daily social sentiment
        social_daily = self.db.query(
            func.date(SocialPost.created_at).label('date'),
            func.avg(SocialSentiment.score).label('avg_score')
        ).join(
            SocialSentiment, SocialPost.id == SocialSentiment.post_id
        ).filter(
            SocialPost.created_at >= cutoff_date
        )
        
        if symbol:
            social_daily = social_daily.filter(SocialPost.symbol == symbol)
        
        social_daily = social_daily.group_by(func.date(SocialPost.created_at)).all()
        
        # Combine daily data
        daily_data = {}
        for row in news_daily:
            date_str = row.date.strftime('%Y-%m-%d')
            daily_data[date_str] = {
                'date': date_str,
                'news_score': float(row.avg_score),
                'social_score': 0.0
            }
        
        for row in social_daily:
            date_str = row.date.strftime('%Y-%m-%d')
            if date_str in daily_data:
                daily_data[date_str]['social_score'] = float(row.avg_score)
            else:
                daily_data[date_str] = {
                    'date': date_str,
                    'news_score': 0.0,
                    'social_score': float(row.avg_score)
                }
        
        # Sort by date
        sorted_data = sorted(daily_data.values(), key=lambda x: x['date'])
        
        return {
            'symbol': symbol,
            'period_days': days,
            'daily_sentiment': sorted_data
        }
