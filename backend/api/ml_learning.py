"""
ML Learning API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from sqlalchemy.orm import Session

from typing import Optional

from datetime import datetime



from app.database import get_db

from models.ml_models import (

    PatternAnalysisRequest,

    StrategyOptimizationRequest,

    TradePatternResponse,

    LearnedStrategyResponse,

    LearningSessionResponse

)

from services.learning_service import LearningService

from services.pattern_analyzer import PatternAnalyzer

from services.strategy_optimizer import StrategyOptimizer



router = APIRouter(prefix="/api/ml", tags=["Machine Learning"])





@router.post("/learn/full-cycle")

async def run_full_learning_cycle(

    strategy_name: str = Query(default="sentiment_based_v1"),

    start_date: Optional[datetime] = None,

    end_date: Optional[datetime] = None,

    db: Session = Depends(get_db)

):
    """Train model endpoint"""
    try:

        learning_service = LearningService(db)

        result = learning_service.run_full_learning_cycle(

            start_date=start_date,

            end_date=end_date,

            strategy_name=strategy_name

        )

        

        if result['status'] == 'failed':

            raise HTTPException(status_code=500, detail=result.get('error'))

        

        return result

        

    except Exception as e:

        raise HTTPException(status_code=500, detail=str(e))





@router.post("/patterns/extract")

async def extract_patterns(

    request: PatternAnalysisRequest,

    db: Session = Depends(get_db)

):

    """API endpoint"""

    try:

        analyzer = PatternAnalyzer(db)

        patterns_count = analyzer.extract_patterns_from_trades(

            start_date=request.start_date,

            end_date=request.end_date,

            symbols=request.symbols

        )

        

        return {

            'status': 'success',
            'patterns_extracted': patterns_count,
            'message': f'{patterns_count} patterns extracted'
        }
    except Exception as e:
        logger.error(f"Pattern extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/patterns/analyze")

async def analyze_patterns(

    request: PatternAnalysisRequest,

    db: Session = Depends(get_db)

):

    """API endpoint"""

    try:

        learning_service = LearningService(db)

        result = learning_service.run_pattern_analysis_only(

            symbol=request.symbols[0] if request.symbols else None

        )

        

        if result['status'] == 'failed':

            raise HTTPException(status_code=500, detail=result.get('error'))

        

        return result

        

    except Exception as e:

        raise HTTPException(status_code=500, detail=str(e))





@router.get("/patterns/statistics")

async def get_pattern_statistics(

    symbol: Optional[str] = None,

    db: Session = Depends(get_db)

):

    """API endpoint"""

    try:

        analyzer = PatternAnalyzer(db)

        stats = analyzer.get_pattern_statistics(symbol=symbol)

        return stats

        

    except Exception as e:

        raise HTTPException(status_code=500, detail=str(e))





@router.post("/strategy/optimize")

async def optimize_strategy(

    request: StrategyOptimizationRequest,

    db: Session = Depends(get_db)

):

    """?�략 최적??""

    try:

        optimizer = StrategyOptimizer(db)

        strategy = optimizer.optimize_strategy(

            strategy_name=request.strategy_name,

            min_profit_threshold=request.min_profit_threshold,

            optimization_metric=request.optimization_metric

        )

        

        return LearnedStrategyResponse.from_orm(strategy)

        

    except Exception as e:

        raise HTTPException(status_code=500, detail=str(e))





@router.get("/strategy/active/{strategy_name}", response_model=LearnedStrategyResponse)

async def get_active_strategy(

    strategy_name: str,

    db: Session = Depends(get_db)

):
    """API endpoint"""
    try:

        optimizer = StrategyOptimizer(db)

        strategy = optimizer.get_active_strategy(strategy_name)

        

        if not strategy:

            raise HTTPException(status_code=404, detail="Active strategy not found")

        

        return LearnedStrategyResponse.from_orm(strategy)

        

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(status_code=500, detail=str(e))





@router.get("/strategy/history/{strategy_name}")

async def get_strategy_history(

    strategy_name: str,

    db: Session = Depends(get_db)

):

    """API endpoint"""

    try:

        optimizer = StrategyOptimizer(db)

        strategies = optimizer.get_strategy_history(strategy_name)

        

        return [LearnedStrategyResponse.from_orm(s) for s in strategies]

        

    except Exception as e:

        raise HTTPException(status_code=500, detail=str(e))





@router.get("/strategy/compare")

async def compare_strategies(

    strategy1_id: int,

    strategy2_id: int,

    db: Session = Depends(get_db)

):

    """API endpoint"""

    try:

        optimizer = StrategyOptimizer(db)

        comparison = optimizer.compare_strategies(strategy1_id, strategy2_id)

        

        if 'error' in comparison:

            raise HTTPException(status_code=404, detail=comparison['error'])

        

        return comparison

        

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(status_code=500, detail=str(e))





@router.get("/sessions/history")

async def get_learning_history(

    limit: int = Query(default=10, ge=1, le=100),

    db: Session = Depends(get_db)

):

    """API endpoint"""

    try:

        learning_service = LearningService(db)

        history = learning_service.get_learning_history(limit=limit)

        return history

        

    except Exception as e:

        raise HTTPException(status_code=500, detail=str(e))





@router.get("/health")

async def ml_health_check(db: Session = Depends(get_db)):

    """API endpoint"""

    try:

        analyzer = PatternAnalyzer(db)

        stats = analyzer.get_pattern_statistics()

        

        return {

            'status': 'healthy',

            'total_patterns': stats.get('total_patterns', 0),

            'win_rate': stats.get('win_rate', 0),

            'message': 'ML learning system is operational'

        }

        

    except Exception as e:

        return {

            'status': 'unhealthy',

            'error': str(e)

        }

