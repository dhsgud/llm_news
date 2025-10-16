"""
Task 26 Verification Script
"""
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from models.trade_history import TradeHistory
from models.ml_models import TradePattern, LearnedStrategy
from services.pattern_analyzer import PatternAnalyzer
from services.strategy_optimizer import StrategyOptimizer
from services.learning_service import LearningService

# Test database
TEST_DATABASE_URL = "sqlite:///./test_ml_verification.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def setup_test_data(db):
    """Create sample trade data"""
    print("Setting up test data...")
    base_time = datetime.utcnow() - timedelta(days=30)
    
    # Create 5 winning trades
    for i in range(5):
        buy = TradeHistory(
            user_id="test", order_id=f"BUY_{i}", symbol=f"STOCK{i}",
            action="BUY", trade_type="BUY", quantity=100,
            price=100.0, executed_price=100.0, total_amount=10000.0,
            executed_at=base_time + timedelta(days=i*2),
            status="COMPLETED", signal_ratio=85
        )
        sell = TradeHistory(
            user_id="test", order_id=f"SELL_{i}", symbol=f"STOCK{i}",
            action="SELL", trade_type="SELL", quantity=100,
            price=105.0, executed_price=105.0, total_amount=10500.0,
            executed_at=base_time + timedelta(days=i*2, hours=24),
            status="COMPLETED", signal_ratio=30
        )
        db.add(buy)
        db.add(sell)
    
    # Create 3 losing trades
    for i in range(3):
        buy = TradeHistory(
            user_id="test", order_id=f"BUY_{i+10}", symbol=f"STOCK{i+10}",
            action="BUY", trade_type="BUY", quantity=100,
            price=100.0, executed_price=100.0, total_amount=10000.0,
            executed_at=base_time + timedelta(days=i*2+10),
            status="COMPLETED", signal_ratio=75
        )
        sell = TradeHistory(
            user_id="test", order_id=f"SELL_{i+10}", symbol=f"STOCK{i+10}",
            action="SELL", trade_type="SELL", quantity=100,
            price=97.0, executed_price=97.0, total_amount=9700.0,
            executed_at=base_time + timedelta(days=i*2+10, hours=12),
            status="COMPLETED", signal_ratio=25
        )
        db.add(buy)
        db.add(sell)
    
    db.commit()
    print("[OK] Test data created: 8 trade pairs")

def test_pattern_extraction(db):
    """Test pattern extraction"""
    print("\n1. Testing pattern extraction...")
    analyzer = PatternAnalyzer(db)
    count = analyzer.extract_patterns_from_trades()
    print(f"[OK] Extracted {count} patterns")
    return count > 0

def test_pattern_analysis(db):
    """Test pattern analysis"""
    print("\n2. Testing pattern analysis...")
    analyzer = PatternAnalyzer(db)
    insights = analyzer.analyze_patterns(min_samples=5)
    print(f"[OK] Win rate: {insights.win_rate}%")
    print(f"[OK] Total patterns: {insights.total_patterns}")
    return insights.total_patterns > 0

def test_strategy_optimization(db):
    """Test strategy optimization"""
    print("\n3. Testing strategy optimization...")
    optimizer = StrategyOptimizer(db)
    strategy = optimizer.optimize_strategy("test_strategy")
    print(f"[OK] Strategy created: {strategy.strategy_name} v{strategy.version}")
    print(f"[OK] Buy threshold: {strategy.buy_threshold}")
    print(f"[OK] Sell threshold: {strategy.sell_threshold}")
    return strategy is not None

def test_full_learning_cycle(db):
    """Test full learning cycle"""
    print("\n4. Testing full learning cycle...")
    learning_service = LearningService(db)
    result = learning_service.run_full_learning_cycle(strategy_name="full_test")
    
    if result['status'] == 'success':
        print(f"[OK] Learning cycle completed")
        print(f"[OK] Patterns extracted: {result['patterns_extracted']}")
        print(f"[OK] Win rate: {result['insights']['win_rate']}%")
        return True
    else:
        print(f"[FAIL] Learning cycle failed: {result.get('error')}")
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("Task 26: ML Learning System Verification")
    print("="*60)
    
    # Setup
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        setup_test_data(db)
        
        # Run tests
        tests = [
            test_pattern_extraction(db),
            test_pattern_analysis(db),
            test_strategy_optimization(db),
            test_full_learning_cycle(db)
        ]
        
        # Summary
        print("\n" + "="*60)
        passed = sum(tests)
        total = len(tests)
        print(f"Tests passed: {passed}/{total}")
        
        if passed == total:
            print("[OK] All tests passed!")
            return 0
        else:
            print("[FAIL] Some tests failed")
            return 1
            
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

if __name__ == "__main__":
    sys.exit(main())
