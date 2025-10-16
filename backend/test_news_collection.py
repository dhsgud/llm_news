#!/usr/bin/env python3
"""
Test script for news collection API
"""

import sys
import requests
import time

# Add backend to path
sys.path.insert(0, '.')

API_BASE_URL = "http://localhost:8000"


def test_news_collection():
    """Test the news collection endpoints"""
    
    print("=" * 60)
    print("Testing News Collection API")
    print("=" * 60)
    
    # 1. Test health check
    print("\n1. Testing health check...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 2. Test get stats
    print("\n2. Testing get stats...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/news/stats", params={"days": 7})
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 3. Test get articles
    print("\n3. Testing get articles...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/news/articles", params={"limit": 5})
        print(f"   Status: {response.status_code}")
        data = response.json()
        print(f"   Found {len(data.get('articles', []))} articles")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 4. Test get logs
    print("\n4. Testing get logs...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/news/logs")
        print(f"   Status: {response.status_code}")
        data = response.json()
        print(f"   Found {len(data.get('logs', []))} log entries")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 5. Test news collection (optional - takes time)
    print("\n5. Testing news collection (skipped - run manually)...")
    print("   To test collection, run:")
    print(f"   curl -X POST '{API_BASE_URL}/api/news/collect?days=1&query=finance'")
    
    print("\n" + "=" * 60)
    print("Tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_news_collection()
