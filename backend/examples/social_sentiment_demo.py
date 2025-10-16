"""
Social Sentiment Analysis Demo
Demonstrates how to use the social sentiment analysis features
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from models.social_models import SocialPost, SocialPostCreate
from services.social_data_collector import SocialDataCollector
from services.social_sentiment_analyzer import SocialSentimentAnalyzer
from services.integrated_sentiment_service import IntegratedSentimentService
from services.llm_client import LlamaCppClient
from config import settings


# Database setup
DATABASE_URL = "sqlite:///./market_analyzer.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def demo_data_collection():
    """Demo: Collect social media data"""
    print("\n" + "="*60)
    print("Demo 1: Social Media Data Collection")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        collector = SocialDataCollector(db)
        
        # Collect posts for specific symbols
        print("\n1. Collecting posts for AAPL and TSLA...")
        stats = collector.collect_all(symbols=["AAPL", "TSLA"])
        
        print(f"\nCollection Results:")
        print(f"  Twitter posts: {stats['twitter']}")
        print(f"  Reddit posts: {stats['reddit']}")
        print(f"  Total: {stats['total']}")
        
        # Show some collected posts
        posts = db.query(SocialPost).limit(5).all()
        print(f"\nSample Posts:")
        for post in posts:
            print(f"\n  Platform: {post.platform}")
            print(f"  Symbol: {post.symbol}")
            print(f"  Content: {post.content[:100]}...")
            print(f"  Engagement: {post.likes} likes, {post.comments} comments")
        
    finally:
        db.close()


def demo_sentiment_analysis():
    """Demo: Analyze sentiment of social posts"""
    print("\n" + "="*60)
    print("Demo 2: Social Sentiment Analysis")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        llm_client = LlamaCppClient(
            base_url=settings.LLAMA_CPP_URL,
            timeout=settings.LLAMA_CPP_TIMEOUT
        )
        analyzer = SocialSentimentAnalyzer(db, llm_client)
        
        # Get unanalyzed posts
        print("\n1. Finding unanalyzed posts...")
        unanalyzed = analyzer.get_unanalyzed_posts(limit=10)
        print(f"Found {len(unanalyzed)} unanalyzed posts")
        
        if unanalyzed:
            # Analyze posts
            print("\n2. Analyzing sentiment...")
            analyzed_count = analyzer.analyze_batch(unanalyzed)
            print(f"Analyzed {analyzed_count} posts")
            
            # Show results
            from models.social_models import SocialSentiment
            recent_sentiments = db.query(SocialSentiment).order_by(
                SocialSentiment.analyzed_at.desc()
            ).limit(5).all()
            
            print("\nRecent Sentiment Analysis:")
            for sentiment in recent_sentiments:
                post = db.query(SocialPost).filter(
                    SocialPost.id == sentiment.post_id
                ).first()
                print(f"\n  Post: {post.content[:80]}...")
                print(f"  Sentiment: {sentiment.sentiment}")
                print(f"  Score: {sentiment.score:.2f}")
                print(f"  Confidence: {sentiment.confidence:.2f}")
                print(f"  Reasoning: {sentiment.reasoning}")
        
    finally:
        db.close()


def demo_aggregated_sentiment():
    """Demo: Get aggregated sentiment summary"""
    print("\n" + "="*60)
    print("Demo 3: Aggregated Sentiment Summary")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        llm_client = LlamaCppClient(
            base_url=settings.LLAMA_CPP_URL,
            timeout=settings.LLAMA_CPP_TIMEOUT
        )
        analyzer = SocialSentimentAnalyzer(db, llm_client)
        
        # Get summary for AAPL
        print("\n1. Getting sentiment summary for AAPL...")
        summaries = analyzer.get_sentiment_summary(symbol="AAPL", days=7)
        
        for summary in summaries:
            print(f"\nPlatform: {summary.platform}")
            print(f"  Total posts: {summary.total_posts}")
            print(f"  Average sentiment: {summary.avg_sentiment:.2f}")
            print(f"  Distribution:")
            print(f"    Positive: {summary.sentiment_distribution['positive']}")
            print(f"    Negative: {summary.sentiment_distribution['negative']}")
            print(f"    Neutral: {summary.sentiment_distribution['neutral']}")
            print(f"  Total engagement: {summary.total_engagement}")
            print(f"  Trending score: {summary.trending_score:.3f}")
        
        # Get overall market sentiment
        print("\n2. Getting overall market sentiment...")
        market_summaries = analyzer.get_sentiment_summary(symbol=None, days=7)
        
        for summary in market_summaries:
            print(f"\nPlatform: {summary.platform}")
            print(f"  Total posts: {summary.total_posts}")
            print(f"  Average sentiment: {summary.avg_sentiment:.2f}")
        
    finally:
        db.close()


def demo_integrated_sentiment():
    """Demo: Combined news and social sentiment"""
    print("\n" + "="*60)
    print("Demo 4: Integrated Sentiment Analysis")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        llm_client = LlamaCppClient(
            base_url=settings.LLAMA_CPP_URL,
            timeout=settings.LLAMA_CPP_TIMEOUT
        )
        service = IntegratedSentimentService(db, llm_client)
        
        # Get combined sentiment
        print("\n1. Getting combined sentiment for AAPL...")
        combined = service.get_combined_sentiment(symbol="AAPL", days=7)
        
        print(f"\nNews Sentiment:")
        print(f"  Articles analyzed: {combined['news_sentiment']['count']}")
        print(f"  Average score: {combined['news_sentiment']['avg_score']:.2f}")
        print(f"  Positive: {combined['news_sentiment']['positive']}")
        print(f"  Negative: {combined['news_sentiment']['negative']}")
        
        print(f"\nSocial Sentiment:")
        for platform, data in combined['social_sentiment'].items():
            print(f"  {platform.capitalize()}:")
            print(f"    Posts: {data['post_count']}")
            print(f"    Avg sentiment: {data['avg_sentiment']:.2f}")
        
        print(f"\nCombined Score: {combined['combined_score']:.2f}")
        
        # Check for divergence
        print("\n2. Checking sentiment divergence...")
        divergence = service.get_sentiment_divergence(symbol="AAPL", days=7)
        
        print(f"\nDivergence Analysis:")
        print(f"  News score: {divergence['news_score']:.2f}")
        print(f"  Social score: {divergence['social_score']:.2f}")
        print(f"  Divergence: {divergence['divergence']:.2f}")
        print(f"  Interpretation: {divergence['interpretation']}")
        print(f"  Recommendation: {divergence['recommendation']}")
        
        # Get sentiment trend
        print("\n3. Getting sentiment trend...")
        trend = service.get_sentiment_trend(symbol="AAPL", days=7)
        
        print(f"\nSentiment Trend (last {trend['period_days']} days):")
        for day in trend['daily_sentiment']:
            print(f"  {day['date']}: News={day['news_score']:.2f}, Social={day['social_score']:.2f}")
        
    finally:
        db.close()


def demo_trending_symbols():
    """Demo: Get trending stock symbols"""
    print("\n" + "="*60)
    print("Demo 5: Trending Symbols")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        from models.social_models import SocialPost, SocialSentiment
        from sqlalchemy import func, desc
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=1)
        
        # Get trending symbols
        print("\n1. Finding trending symbols (last 24 hours)...")
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
        ).limit(10).all()
        
        print("\nTop Trending Symbols:")
        for i, row in enumerate(trending, 1):
            print(f"\n{i}. {row.symbol}")
            print(f"   Posts: {row.post_count}")
            print(f"   Engagement: {row.engagement}")
            print(f"   Avg Sentiment: {row.avg_sentiment:.2f}")
        
    finally:
        db.close()


def main():
    """Run all demos"""
    print("\n" + "="*60)
    print("Social Sentiment Analysis - Demo")
    print("="*60)
    
    print("\nThis demo showcases the social sentiment analysis features:")
    print("1. Data collection from Twitter and Reddit")
    print("2. LLM-based sentiment analysis")
    print("3. Aggregated sentiment summaries")
    print("4. Integration with news sentiment")
    print("5. Trending symbol detection")
    
    print("\nNote: Make sure you have configured:")
    print("- TWITTER_BEARER_TOKEN in .env")
    print("- REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env")
    print("- llama.cpp server running")
    
    input("\nPress Enter to start the demo...")
    
    try:
        # Run demos
        demo_data_collection()
        input("\nPress Enter to continue to sentiment analysis...")
        
        demo_sentiment_analysis()
        input("\nPress Enter to continue to aggregated sentiment...")
        
        demo_aggregated_sentiment()
        input("\nPress Enter to continue to integrated sentiment...")
        
        demo_integrated_sentiment()
        input("\nPress Enter to continue to trending symbols...")
        
        demo_trending_symbols()
        
        print("\n" + "="*60)
        print("Demo completed successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"\nError during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
