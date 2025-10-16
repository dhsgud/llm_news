import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("Testing imports...")

try:
    from services.llm_client import LlamaCppClient
    from models import SentimentAnalysis, NewsArticle, SentimentResult
    print("??backend imports OK")
except Exception as e:
    print(f"??backend import failed: {e}")
    import traceback
    traceback.print_exc()

try:
    from services.trend_aggregator import TrendAggregator
    print(f"??TrendAggregator imported: {TrendAggregator}")
except Exception as e:
    print(f"??TrendAggregator import failed: {e}")
    import traceback
    traceback.print_exc()
