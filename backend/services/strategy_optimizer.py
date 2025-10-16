"""

Strategy Optimizer - _략 최적"
"""

import logging

from datetime import datetime

from typing import Dict, Any, Optional, List

from sqlalchemy.orm import Session

from sqlalchemy import func



from models.ml_models import TradePattern, LearnedStrategy, PatternInsights

from services.pattern_analyzer import PatternAnalyzer



logger = logging.getLogger(__name__)





class StrategyOptimizer:

    """?�략 최적?�기"""

    

    def __init__(self, db: Session):

        self.db = db

        self.pattern_analyzer = PatternAnalyzer(db)

    

    def optimize_strategy(

        self,

        strategy_name: str = "sentiment_based_v1",

        min_profit_threshold: float = 2.0,

        optimization_metric: str = "sharpe_ratio"

    ) -> LearnedStrategy:

        """

        거래 _턴 기반 "
        """

        try:

            logger.info(f"Starting strategy optimization: {strategy_name}")

            

            # _턴 분석"

            insights = self.pattern_analyzer.analyze_patterns(min_samples=5)

            

            if insights.total_patterns < 5:

                logger.warning("Insufficient data for optimization")

                return self._create_default_strategy(strategy_name)

            

            # 최적 _라미터 계산

            optimal_params = self._calculate_optimal_parameters(

                insights, min_profit_threshold

            )

            

            # "
            logger.info(f"Strategy optimized: {strategy_name} v{new_strategy.version}")

            return new_strategy

            

        except Exception as e:

            logger.error(f"Error optimizing strategy: {e}")

            self.db.rollback()

            raise

    

    def _calculate_optimal_parameters(

        self,

        insights: PatternInsights,

        min_profit_threshold: float

    ) -> Dict[str, Any]:

        """최적 ?�라미터 계산"""

        

        # _률 기반 "
        """?�과 지??계산"""

        

        win_rate = insights.win_rate / 100.0

        avg_win = insights.avg_winning_profit

        avg_loss = abs(insights.avg_losing_loss)

        

        # 기�_"
        """기본 ?�략 ?�성 (?�이??부�???"""

        

        default_strategy = LearnedStrategy(

            strategy_name=strategy_name,

            version=1,

            buy_threshold=80.0,

            sell_threshold=20.0,

            position_size_multiplier=1.0,

            stop_loss_percent=3.0,

            take_profit_percent=5.0,

            max_holding_hours=48.0,

            vix_adjustment_factor=1.0,

            parameters={'note': 'Default strategy - insufficient training data'},

            performance_metrics={'status': 'untrained'},

            training_samples=0,

            is_active=True,

            created_at=datetime.utcnow(),

            updated_at=datetime.utcnow()

        )

        

        self.db.add(default_strategy)

        self.db.commit()

        self.db.refresh(default_strategy)

        

        logger.info(f"Created default strategy: {strategy_name}")

        return default_strategy

    

    def get_active_strategy(self, strategy_name: str) -> Optional[LearnedStrategy]:

        """?�성 ?�략 조회"""

        return self.db.query(LearnedStrategy).filter(

            LearnedStrategy.strategy_name == strategy_name,

            LearnedStrategy.is_active == True

        ).first()

    

    def get_strategy_history(self, strategy_name: str) -> List[LearnedStrategy]:

        """?�략 버전 ?�스?�리 조회"""

        return self.db.query(LearnedStrategy).filter(

            LearnedStrategy.strategy_name == strategy_name

        ).order_by(LearnedStrategy.version.desc()).all()

    

    def compare_strategies(

        self,

        strategy1_id: int,

        strategy2_id: int

    ) -> Dict[str, Any]:

        """???�략 비교"""

        

        s1 = self.db.query(LearnedStrategy).filter(LearnedStrategy.id == strategy1_id).first()

        s2 = self.db.query(LearnedStrategy).filter(LearnedStrategy.id == strategy2_id).first()

        

        if not s1 or not s2:

            return {'error': 'Strategy not found'}

        

        comparison = {

            'strategy1': {

                'name': f"{s1.strategy_name} v{s1.version}",

                'buy_threshold': s1.buy_threshold,

                'sell_threshold': s1.sell_threshold,

                'performance': s1.performance_metrics

            },

            'strategy2': {

                'name': f"{s2.strategy_name} v{s2.version}",

                'buy_threshold': s2.buy_threshold,

                'sell_threshold': s2.sell_threshold,

                'performance': s2.performance_metrics

            },

            'recommendation': self._recommend_better_strategy(s1, s2)

        }

        

        return comparison

    

    def _recommend_better_strategy(

        self,

        s1: LearnedStrategy,

        s2: LearnedStrategy

    ) -> str:

        """???��? ?�략 추천"""

        

        if not s1.performance_metrics or not s2.performance_metrics:

            return "?�과 ?�이?��? 부족합?�다."

        

        m1 = s1.performance_metrics

        m2 = s2.performance_metrics

        

        # _프 비율 비교"

        sharpe1 = m1.get('sharpe_ratio', 0)

        sharpe2 = m2.get('sharpe_ratio', 0)

        

        if sharpe1 > sharpe2 * 1.1:

            return f"{s1.strategy_name} v{s1.version}?????�수?�니??(?�프 비율: {sharpe1:.2f} vs {sharpe2:.2f})"

        elif sharpe2 > sharpe1 * 1.1:

            return f"{s2.strategy_name} v{s2.version}?????�수?�니??(?�프 비율: {sharpe2:.2f} vs {sharpe1:.2f})"

        else:

            return "???�략???�과가 비슷?�니??"

