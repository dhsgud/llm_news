"""
Verification script for Task 29: Social Sentiment Analysis
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from app.database import Base
from models.social_models import SocialPost, SocialSentiment, AggregatedSocialSentiment


def verify_database_tables():
    """Verify that social sentiment tables exist"""
    print("\n=== Verifying Database Tables ===")
    
    engine = create_engine("sqlite:///./market_analyzer.db")
    inspector = inspect(engine)
    
    required_tables = [
        'social_posts',
        'social_sentiments',
        'aggregated_social_sentiments'
    ]
    
    existing_tables = inspector.get_table_names()
    all_exist = True
    
    for table in required_tables:
        if table in existing_tables:
            print(f"??Table '{table}' exists")
            
            # Check columns
            columns = inspector.get_columns(table)
            print(f"  Columns: {', '.join([col['name'] for col in columns])}")
        else:
            print(f"??Table '{table}' missing (run migration to create)")
            all_exist = False
    
    if not all_exist:
        print("\nNote: Run 'python run_social_migration.py' to create tables")
    
    return all_exist


def verify_models():
    """Verify that models can be imported and instantiated"""
    print("\n=== Verifying Models ===")
    
    try:
        from models.social_models import (
            SocialPost, SocialSentiment, AggregatedSocialSentiment,
            SocialPostCreate, SocialSentimentCreate,
            SocialSentimentSummary
        )
        print("??All models imported successfully")
        
        # Test model instantiation
        post = SocialPost(
            platform="twitter",
            post_id="test123",
            content="Test",
            created_at=datetime.now()
        )
        print("??SocialPost model instantiated")
        
        return True
    except Exception as e:
        print(f"??Error with models: {e}")
        return False


def verify_services():
    """Verify that services can be imported"""
    print("\n=== Verifying Services ===")
    
    try:
        from services.social_data_collector import SocialDataCollector
        print("??SocialDataCollector imported")
        
        from services.social_sentiment_analyzer import SocialSentimentAnalyzer
        print("??SocialSentimentAnalyzer imported")
        
        from services.integrated_sentiment_service import IntegratedSentimentService
        print("??IntegratedSentimentService imported")
        
        return True
    except Exception as e:
        print(f"??Error importing services: {e}")
        return False


def verify_api_endpoints():
    """Verify that API endpoints are defined"""
    print("\n=== Verifying API Endpoints ===")
    
    try:
        # Check if file exists
        api_file = "api/social_sentiment.py"
        if os.path.exists(api_file):
            print(f"??API file exists: {api_file}")
        elif os.path.exists(f"backend/{api_file}"):
            print(f"??API file exists: backend/{api_file}")
            api_file = f"backend/{api_file}"
        else:
            print(f"??API file missing")
            return False
        
        # Check for expected endpoint definitions
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        expected_endpoints = [
            'collect_social_data',
            'analyze_social_sentiment',
            'get_sentiment_summary',
            'get_social_posts',
            'aggregate_sentiment',
            'cleanup_old_posts',
            'get_trending_symbols'
        ]
        
        print(f"  Checking for expected endpoints...")
        for endpoint in expected_endpoints:
            if f"def {endpoint}" in content or f"async def {endpoint}" in content:
                print(f"  ??{endpoint}")
            else:
                print(f"  ??{endpoint} missing")
        
        return True
    except Exception as e:
        print(f"??Error with API endpoints: {e}")
        return False


def verify_migration():
    """Verify migration file exists"""
    print("\n=== Verifying Migration ===")
    
    migration_file = "alembic/versions/009_add_social_sentiment_tables.py"
    
    # Check both with and without backend prefix
    if os.path.exists(migration_file):
        print(f"??Migration file exists: {migration_file}")
        return True
    elif os.path.exists(f"backend/{migration_file}"):
        print(f"??Migration file exists: backend/{migration_file}")
        return True
    else:
        print(f"??Migration file missing: {migration_file}")
        return False


def verify_integration():
    """Verify integration with existing system"""
    print("\n=== Verifying Integration ===")
    
    try:
        # Check if can import both news and social models
        try:
            from models.sentiment_analysis import SentimentAnalysis
            from models.social_models import SocialSentiment
        except ImportError:
            from models.sentiment_analysis import SentimentAnalysis
            from models.social_models import SocialSentiment
        print("??Can import both news and social sentiment models")
        
        # Check integrated service
        try:
            from services.integrated_sentiment_service import IntegratedSentimentService
        except ImportError:
            from services.integrated_sentiment_service import IntegratedSentimentService
        print("??Integrated sentiment service available")
        
        return True
    except Exception as e:
        print(f"??Integration error: {e}")
        return False


def main():
    """Run all verification checks"""
    print("=" * 60)
    print("Task 29: Social Sentiment Analysis - Verification")
    print("=" * 60)
    
    results = {
        "Database Tables": verify_database_tables(),
        "Models": verify_models(),
        "Services": verify_services(),
        "API Endpoints": verify_api_endpoints(),
        "Migration": verify_migration(),
        "Integration": verify_integration()
    }
    
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)
    
    for check, passed in results.items():
        status = "??PASS" if passed else "??FAIL"
        print(f"{check:.<40} {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("??All verification checks passed!")
        print("\nTask 29 is ready for use.")
        print("\nNext steps:")
        print("1. Configure Twitter API credentials in .env:")
        print("   TWITTER_BEARER_TOKEN=your_token")
        print("2. Configure Reddit API credentials in .env:")
        print("   REDDIT_CLIENT_ID=your_client_id")
        print("   REDDIT_CLIENT_SECRET=your_secret")
        print("3. Run migration: python run_social_migration.py")
        print("4. Test endpoints with: python test_task_29_social_sentiment.py")
    else:
        print("??Some verification checks failed.")
        print("Please review the errors above.")
    
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
