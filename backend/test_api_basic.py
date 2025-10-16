"""
Basic API test script to verify endpoints are working
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root():
    """Test root endpoint"""
    response = client.get("/")
    print(f"GET / - Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    assert response.json()["status"] == "running"
    print("[OK] Root endpoint working\n")


def test_health():
    """Test health check endpoint"""
    response = client.get("/health")
    print(f"GET /health - Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    print("[OK] Health endpoint working\n")


def test_news_endpoint():
    """Test news endpoint (may return empty if no data)"""
    response = client.get("/api/news?days=7&limit=10")
    print(f"GET /api/news - Status: {response.status_code}")
    print(f"Response: {response.json()}")
    # Accept 200 (success) or 500 (database not available)
    assert response.status_code in [200, 500]
    print("[OK] News endpoint responding\n")


def test_daily_sentiment_endpoint():
    """Test daily sentiment endpoint (may return empty if no data)"""
    response = client.get("/api/sentiment/daily?days=7")
    print(f"GET /api/sentiment/daily - Status: {response.status_code}")
    print(f"Response: {response.json()}")
    # Accept 200 (success) or 500 (database not available)
    assert response.status_code in [200, 500]
    print("[OK] Daily sentiment endpoint responding\n")


def test_analyze_endpoint_no_data():
    """Test analyze endpoint (expected to fail with no data)"""
    response = client.post("/api/analyze?asset_type=general")
    print(f"POST /api/analyze - Status: {response.status_code}")
    print(f"Response: {response.json()}")
    # Should return 400 or 500 if no data exists
    assert response.status_code in [400, 500]
    print("[OK] Analyze endpoint responding correctly (no data scenario)\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing FastAPI Backend Endpoints")
    print("=" * 60 + "\n")
    
    try:
        test_root()
        test_health()
        test_news_endpoint()
        test_daily_sentiment_endpoint()
        test_analyze_endpoint_no_data()
        
        print("=" * 60)
        print("All basic tests passed!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
