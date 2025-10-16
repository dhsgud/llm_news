"""
Example: Signal Generation with Database Integration

This example shows how to integrate the signal generator with
the database models and sentiment analysis results.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
from services.signal_generator import SignalCalculator


def example_with_database_results():
    """
    Example showing how to use signal generator with database query results.
    
    This simulates what would happen in a real API endpoint that:
    1. Queries sentiment analysis results from the database
    2. Passes them to the signal generator
    3. Returns buy/sell ratio to the frontend
    """
    print("=" * 70)
    print("Signal Generation with Database Integration")
    print("=" * 70)
    
    # Simulate database query results (SentimentAnalysis model)
    # In real code, this would be:
    # from models import SentimentAnalysis
    # from app.database import get_db
    # 
    # cutoff_date = datetime.now() - timedelta(days=7)
    # results = db.query(SentimentAnalysis).filter(
    #     SentimentAnalysis.analyzed_at >= cutoff_date
    # ).all()
    
    base_date = datetime.now()
    
    # Simulated database results
    db_results = [
        {
            "id": 1,
            "article_id": 101,
            "sentiment": "Positive",
            "score": 1.0,
            "reasoning": "Strong earnings report",
            "analyzed_at": base_date
        },
        {
            "id": 2,
            "article_id": 102,
            "sentiment": "Positive",
            "score": 1.0,
            "reasoning": "Market optimism",
            "analyzed_at": base_date - timedelta(days=1)
        },
        {
            "id": 3,
            "article_id": 103,
            "sentiment": "Negative",
            "score": -1.5,
            "reasoning": "Regulatory concerns",
            "analyzed_at": base_date - timedelta(days=2)
        },
        {
            "id": 4,
            "article_id": 104,
            "sentiment": "Neutral",
            "score": 0.0,
            "reasoning": "Mixed signals",
            "analyzed_at": base_date - timedelta(days=3)
        },
        {
            "id": 5,
            "article_id": 105,
            "sentiment": "Positive",
            "score": 1.0,
            "reasoning": "Innovation announcement",
            "analyzed_at": base_date - timedelta(days=4)
        },
    ]
    
    print(f"\n?�� Processing {len(db_results)} sentiment analysis results from database")
    print(f"?�� Date range: {(base_date - timedelta(days=4)).strftime('%Y-%m-%d')} to {base_date.strftime('%Y-%m-%d')}")
    
    # Initialize signal calculator
    calculator = SignalCalculator()
    
    # Calculate buy/sell ratio
    result = calculator.calculate_buy_sell_ratio(db_results)
    
    # Display results
    print(f"\n?�� Signal Generation Results:")
    print(f"  Buy/Sell Ratio: {result['ratio']}")
    print(f"  Interpretation: {result['interpretation']}")
    print(f"  Raw Signal Score: {result['signal_score']:.2f}")
    print(f"  VIX (normalized): {result['vix_normalized']:.3f}")
    
    print(f"\n?�� Daily Sentiment Breakdown:")
    for date, score in sorted(result['daily_scores'].items(), reverse=True):
        emoji = "?��" if score > 0 else "?��" if score < 0 else "??
        sentiment_type = "Positive" if score > 0 else "Negative" if score < 0 else "Neutral"
        print(f"  {emoji} {date}: {score:+.2f} ({sentiment_type})")
    
    # Simulate API response
    api_response = {
        "buy_sell_ratio": result['ratio'],
        "interpretation": result['interpretation'],
        "signal_score": result['signal_score'],
        "vix_normalized": result['vix_normalized'],
        "daily_scores": result['daily_scores'],
        "last_updated": datetime.now().isoformat(),
        "data_points": len(db_results)
    }
    
    print(f"\n?�� API Response (JSON):")
    import json
    print(json.dumps(api_response, indent=2, default=str))
    
    return api_response


def example_api_endpoint_simulation():
    """
    Simulate a FastAPI endpoint that uses the signal generator.
    """
    print("\n" + "=" * 70)
    print("FastAPI Endpoint Simulation")
    print("=" * 70)
    
    print("""
    # This is how the signal generator would be used in an API endpoint:
    
    from fastapi import APIRouter, Depends
    from sqlalchemy.orm import Session
    from datetime import datetime, timedelta
    
    from app.database import get_db
    from models import SentimentAnalysis
    from services.signal_generator import SignalCalculator
    
    router = APIRouter()
    
    @router.post("/api/analyze")
    async def analyze_market(db: Session = Depends(get_db)):
        '''
        Analyze market sentiment and return buy/sell ratio.
        '''
        # Query sentiment data from last 7 days
        cutoff_date = datetime.now() - timedelta(days=7)
        sentiment_results = db.query(SentimentAnalysis).filter(
            SentimentAnalysis.analyzed_at >= cutoff_date
        ).all()
        
        # Convert to dict format
        sentiment_data = [
            {
                "sentiment": result.sentiment,
                "analyzed_at": result.analyzed_at,
                "score": result.score
            }
            for result in sentiment_results
        ]
        
        # Calculate signal
        calculator = SignalCalculator()
        signal_result = calculator.calculate_buy_sell_ratio(sentiment_data)
        
        # Return response
        return {
            "buy_sell_ratio": signal_result['ratio'],
            "trend_summary": signal_result['interpretation'],
            "last_updated": datetime.now(),
            "vix": signal_result['vix_normalized'],
            "daily_scores": signal_result['daily_scores']
        }
    """)
    
    print("\n??The signal generator is ready for API integration!")


def example_caching_strategy():
    """
    Show how to implement caching for signal calculations.
    """
    print("\n" + "=" * 70)
    print("Caching Strategy Example")
    print("=" * 70)
    
    print("""
    # To avoid recalculating signals frequently, implement caching:
    
    from models import AnalysisCache
    import json
    
    def get_or_calculate_signal(db: Session, cache_key: str = "market_signal"):
        '''
        Get cached signal or calculate new one if expired.
        '''
        # Check cache
        cache = db.query(AnalysisCache).filter(
            AnalysisCache.cache_key == cache_key,
            AnalysisCache.expires_at > datetime.now()
        ).first()
        
        if cache:
            # Return cached result
            return json.loads(cache.result_json)
        
        # Calculate new signal
        calculator = SignalCalculator()
        sentiment_data = get_recent_sentiment_data(db)
        result = calculator.calculate_buy_sell_ratio(sentiment_data)
        
        # Cache result for 1 hour
        cache_entry = AnalysisCache(
            cache_key=cache_key,
            result_json=json.dumps(result, default=str),
            expires_at=datetime.now() + timedelta(hours=1)
        )
        db.add(cache_entry)
        db.commit()
        
        return result
    """)
    
    print("\n?�� Caching reduces load and improves response time!")


if __name__ == "__main__":
    print("\n?�� Signal Generator Database Integration Examples\n")
    
    # Run examples
    example_with_database_results()
    example_api_endpoint_simulation()
    example_caching_strategy()
    
    print("\n" + "=" * 70)
    print("??Integration examples completed!")
    print("=" * 70)
    print("\n?�� Next Steps:")
    print("  1. Implement API endpoints in Task 8")
    print("  2. Add caching logic using AnalysisCache model")
    print("  3. Connect to frontend dashboard")
    print("  4. Test with real sentiment analysis data")
    print("=" * 70 + "\n")
