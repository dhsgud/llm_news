"""
Task 26: ML Learning System Tests
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from models.trade_history import TradeHistory
from models.ml_models import TradePattern, LearnedStrategy, LearningSession
from services.pattern_analyzer import PatternAnalyzer
from services.strategy_optimizer import StrategyOptimizer
from services.learning_service import LearningService


# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_ml_learning.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create test database"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_trades(db):
    """Create sample trade history"""
    trades = []
    base_time = datetime.utcnow() - timedelta(days=30)
    
    # Create winning trade pairs
    for i in range(5):
        buy_trade = TradeHistory(
            user_id="test_user",
            order_id=f"BUY_{i}",
            symbol=f"STOCK{i}",
            action="BUY",
            trade_type="BUY",
            quantity=100,
            price=100.0,
            executed_price=100.0,
            total_amount=10000.0,
            executed_at=base_time + timedelta(days=i*2),
            status="COMPLETED",
            signal_ratio=85,
            reasoning="Test buy trade"
        )
        sell_trade = TradeHistory(
            user_id="test_user",
            order_id=f"SELL_{i}",
            symbol=f"STOCK{i}",
            action="SELL",
            trade_type="SELL",
            quantity=100,
            price=105.0,
            executed_price=105.0,  # 5% profit
            total_amount=10500.0,
            executed_at=base_time + timedelta(days=i*2, hours=24),
            status="COMPLETED",
            signal_ratio=30,
            reasoning="Test sell trade"
        )
        db.add(buy_trade)
        db.add(sell_trade)
        trades.extend([buy_trade, sell_trade])
    
    # Create losing trade pairs
    for i in range(3):
        buy_trade = TradeHistory(
            user_id="test_user",
            order_id=f"BUY_{i+10}",
            symbol=f"STOCK{i+10}",
            action="BUY",
            trade_type="BUY",
            quantity=100,
            price=100.0,
            executed_price=100.0,
            total_amount=10000.0,
            executed_at=base_time + timedelta(days=i*2+10),
            status="COMPLETED",
            signal_ratio=75,
            reasoning="Test buy trade"
        )
        sell_trade = TradeHistory(
            user_id="test_user",
            order_id=f"SELL_{i+10}",
            symbol=f"STOCK{i+10}",
            action="SELL",
            trade_type="SELL",
            quantity=100,
            price=97.0,
            executed_price=97.0,  # 3% loss
            total_amount=9700.0,
            executed_at=base_time + timedelta(days=i*2+10, hours=12),
            status="COMPLETED",
            signal_ratio=25,
            reasoning="Test sell trade"
        )
        db.add(buy_trade)
        db.add(sell_trade)
        trades.extend([buy_trade, sell_trade])
    
    db.commit()
    return trades


def test_pattern_extraction(db, sample_trades):
    """Test 1: Pattern extraction from trades"""
    analyzer = PatternAnalyzer(db)
    
    patterns_count = analyzer.extract_patterns_from_trades()
    
    assert patterns_count > 0, "Should extract patterns from trades"
    
    patterns = db.query(TradePattern).all()
    assert len(patterns) == patterns_count
    
    # Check pattern types
    winning = [p for p in patterns if p.pattern_type == 'winning']
    losing = [p for p in patterns if p.pattern_type == 'losing']
    
    assert len(winning) > 0, "Should have winning patterns"
    assert len(losing) > 0, "Should have losing patterns"
    
    print(f"[OK] Extracted {patterns_count} patterns ({len(winning)} winning, {len(losing)} losing)")


def test_pattern_analysis(db, sample_trades):
    """Test 2: Pattern analysis and insights"""
    analyzer = PatternAnalyzer(db)
    
    # Extract patterns first
    analyzer.extract_patterns_from_trades()
    
    # Analyze patterns
    insights = analyzer.analyze_patterns(min_samples=5)
    
    assert insights.total_patterns > 0
    assert insights.win_rate >= 0
    assert insights.win_rate <= 100
    assert len(insights.recommendations) > 0
    
    print(f"??Pattern analysis completed:")
    print(f"  - Total patterns: {insights.total_patterns}")
    print(f"  - Win rate: {insights.win_rate}%")
    print(f"  - Avg winning profit: {insights.avg_winning_profit}%")
    print(f"  - Avg losing loss: {insights.avg_losing_loss}%")
    print(f"  - Recommendations: {len(insights.recommendations)}")


def test_pattern_statistics(db, sample_trades):
    """Test 3: Pattern statistics"""
    analyzer = PatternAnalyzer(db)
    analyzer.extract_patterns_from_trades()
    
    stats = analyzer.get_pattern_statistics()
    
    assert 'total_patterns' in stats
    assert 'win_rate' in stats
    assert 'profit_factor' in stats
    
    print(f"??Pattern statistics:")
    print(f"  - Total: {stats['total_patterns']}")
    print(f"  - Win rate: {stats['win_rate']}%")
    print(f"  - Profit factor: {stats['profit_factor']}")


def test_strategy_optimization(db, sample_trades):
    """Test 4: Strategy optimization"""
    analyzer = PatternAnalyzer(db)
    analyzer.extract_patterns_from_trades()
    
    optimizer = StrategyOptimizer(db)
    strategy = optimizer.optimize_strategy(
        strategy_name="test_strategy",
        min_profit_threshold=2.0
    )
    
    assert strategy is not None
    assert strategy.strategy_name == "test_strategy"
    assert strategy.version == 1
    assert strategy.is_active == True
    assert strategy.buy_threshold > 0
    assert strategy.sell_threshold > 0
    assert strategy.stop_loss_percent > 0
    
    print(f"??Strategy optimized:")
    print(f"  - Name: {strategy.strategy_name} v{strategy.version}")
    print(f"  - Buy threshold: {strategy.buy_threshold}")
    print(f"  - Sell threshold: {strategy.sell_threshold}")
    print(f"  - Stop loss: {strategy.stop_loss_percent}%")
    print(f"  - Training samples: {strategy.training_samples}")


def test_strategy_versioning(db, sample_trades):
    """Test 5: Strategy versioning"""
    analyzer = PatternAnalyzer(db)
    analyzer.extract_patterns_from_trades()
    
    optimizer = StrategyOptimizer(db)
    
    # Create first version
    strategy_v1 = optimizer.optimize_strategy(strategy_name="versioned_strategy")
    assert strategy_v1.version == 1
    assert strategy_v1.is_active == True
    
    # Create second version
    strategy_v2 = optimizer.optimize_strategy(strategy_name="versioned_strategy")
    assert strategy_v2.version == 2
    assert strategy_v2.is_active == True
    
    # Check v1 is deactivated
    db.refresh(strategy_v1)
    assert strategy_v1.is_active == False
    
    print(f"??Strategy versioning works correctly")


def test_get_active_strategy(db, sample_trades):
    """Test 6: Get active strategy"""
    analyzer = PatternAnalyzer(db)
    analyzer.extract_patterns_from_trades()
    
    optimizer = StrategyOptimizer(db)
    created_strategy = optimizer.optimize_strategy(strategy_name="active_test")
    
    active_strategy = optimizer.get_active_strategy("active_test")
    
    assert active_strategy is not None
    assert active_strategy.id == created_strategy.id
    assert active_strategy.is_active == True
    
    print(f"??Active strategy retrieval works")


def test_strategy_history(db, sample_trades):
    """Test 7: Strategy history"""
    analyzer = PatternAnalyzer(db)
    analyzer.extract_patterns_from_trades()
    
    optimizer = StrategyOptimizer(db)
    
    # Create multiple versions
    for i in range(3):
        optimizer.optimize_strategy(strategy_name="history_test")
    
    history = optimizer.get_strategy_history("history_test")
    
    assert len(history) == 3
    assert history[0].version == 3  # Most recent first
    assert history[1].version == 2
    assert history[2].version == 1
    
    print(f"??Strategy history retrieval works ({len(history)} versions)")


def test_strategy_comparison(db, sample_trades):
    """Test 8: Strategy comparison"""
    analyzer = PatternAnalyzer(db)
    analyzer.extract_patterns_from_trades()
    
    optimizer = StrategyOptimizer(db)
    
    strategy1 = optimizer.optimize_strategy(strategy_name="compare_test_1")
    strategy2 = optimizer.optimize_strategy(strategy_name="compare_test_2")
    
    comparison = optimizer.compare_strategies(strategy1.id, strategy2.id)
    
    assert 'strategy1' in comparison
    assert 'strategy2' in comparison
    assert 'recommendation' in comparison
    
    print(f"??Strategy comparison works")
    print(f"  - Recommendation: {comparison['recommendation']}")


def test_full_learning_cycle(db, sample_trades):
    """Test 9: Full learning cycle"""
    learning_service = LearningService(db)
    
    result = learning_service.run_full_learning_cycle(
        strategy_name="full_cycle_test"
    )
    
    assert result['status'] == 'success'
    assert result['patterns_extracted'] > 0
    assert result['patterns_analyzed'] > 0
    assert 'insights' in result
    assert 'optimized_strategy' in result
    
    # Check learning session was created
    session = db.query(LearningSession).filter(
        LearningSession.session_type == 'full_cycle'
    ).first()
    
    assert session is not None
    assert session.status == 'completed'
    assert session.patterns_extracted > 0
    
    print(f"??Full learning cycle completed:")
    print(f"  - Patterns extracted: {result['patterns_extracted']}")
    print(f"  - Patterns analyzed: {result['patterns_analyzed']}")
    print(f"  - Win rate: {result['insights']['win_rate']}%")
    print(f"  - Strategy: {result['optimized_strategy']['name']} v{result['optimized_strategy']['version']}")


def test_pattern_analysis_only(db, sample_trades):
    """Test 10: Pattern analysis only"""
    analyzer = PatternAnalyzer(db)
    analyzer.extract_patterns_from_trades()
    
    learning_service = LearningService(db)
    result = learning_service.run_pattern_analysis_only()
    
    assert result['status'] == 'success'
    assert 'insights' in result
    assert 'statistics' in result
    
    print(f"??Pattern analysis only completed")


def test_learning_history(db, sample_trades):
    """Test 11: Learning history"""
    learning_service = LearningService(db)
    
    # Run multiple learning cycles
    learning_service.run_full_learning_cycle(strategy_name="history_test_1")
    learning_service.run_pattern_analysis_only()
    
    history = learning_service.get_learning_history(limit=10)
    
    assert len(history) >= 2
    assert all('session_type' in h for h in history)
    assert all('status' in h for h in history)
    
    print(f"??Learning history retrieval works ({len(history)} sessions)")


def test_insufficient_data_handling(db):
    """Test 12: Handling insufficient data"""
    optimizer = StrategyOptimizer(db)
    
    # Try to optimize with no data
    strategy = optimizer.optimize_strategy(strategy_name="no_data_test")
    
    assert strategy is not None
    assert strategy.training_samples == 0
    assert 'untrained' in str(strategy.performance_metrics)
    
    print(f"??Insufficient data handling works (default strategy created)")


def test_performance_metrics_calculation(db, sample_trades):
    """Test 13: Performance metrics calculation"""
    analyzer = PatternAnalyzer(db)
    analyzer.extract_patterns_from_trades()
    
    optimizer = StrategyOptimizer(db)
    strategy = optimizer.optimize_strategy(strategy_name="metrics_test")
    
    metrics = strategy.performance_metrics
    
    assert 'win_rate' in metrics
    assert 'expected_value' in metrics
    assert 'profit_factor' in metrics
    assert 'sharpe_ratio' in metrics
    
    print(f"??Performance metrics calculated:")
    print(f"  - Win rate: {metrics['win_rate']}%")
    print(f"  - Expected value: {metrics['expected_value']}%")
    print(f"  - Profit factor: {metrics['profit_factor']}")
    print(f"  - Sharpe ratio: {metrics['sharpe_ratio']}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Task 26: ML Learning System Tests")
    print("="*60 + "\n")
    
    pytest.main([__file__, "-v", "-s"])
