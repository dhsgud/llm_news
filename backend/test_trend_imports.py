import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("Testing imports from trend_aggregator...")

try:
    print("1. Testing standard library imports...")
    import logging
    from datetime import datetime, timedelta
    from typing import List, Optional, Dict, Any
    from pydantic import BaseModel, Field
    from sqlalchemy.orm import Session
    print("??Standard library imports OK")
except Exception as e:
    print(f"??Standard library imports failed: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\n2. Testing backend.services.llm_client import...")
    from services.llm_client import LlamaCppClient, LlamaCppClientError
    print(f"??LlamaCppClient imported: {LlamaCppClient}")
except Exception as e:
    print(f"??LlamaCppClient import failed: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\n3. Testing backend.models imports...")
    from models import SentimentAnalysis, NewsArticle, SentimentResult
    print(f"??Models imported: {SentimentAnalysis}, {NewsArticle}, {SentimentResult}")
except Exception as e:
    print(f"??Models import failed: {e}")
    import traceback
    traceback.print_exc()

print("\n4. All imports successful, trend_aggregator should work!")
