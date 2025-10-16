"""

Learning Service - _합 "
"""

import logging

from datetime import datetime

from typing import Optional, Dict, Any

from sqlalchemy.orm import Session



from models.ml_models import LearningSession

from services.pattern_analyzer import PatternAnalyzer

from services.strategy_optimizer import StrategyOptimizer



logger = logging.getLogger(__name__)





class LearningService:

    """?�합 ?�습 ?�비??""

    

    def __init__(self, db: Session):

        self.db = db

        self.pattern_analyzer = PatternAnalyzer(db)

        self.strategy_optimizer = StrategyOptimizer(db)

    

    def run_full_learning_cycle(

        self,

        start_date: Optional[datetime] = None,

        end_date: Optional[datetime] = None,

        strategy_name: str = "sentiment_based_v1"

    ) -> Dict[str, Any]:

        """

        _체 "
        """

        session = LearningSession(

            session_type='full_cycle',

            start_time=datetime.utcnow(),

            status='running',

            created_at=datetime.utcnow()

        )

        self.db.add(session)

        self.db.commit()

        

        try:

            logger.info("Starting full learning cycle")

            

            # 1. _턴 추출"

            logger.info("Step 1: Extracting patterns from trades")

            patterns_extracted = self.pattern_analyzer.extract_patterns_from_trades(

                start_date=start_date,

                end_date=end_date

            )

            session.patterns_extracted = patterns_extracted

            self.db.commit()

            

            if patterns_extracted < 5:

                raise ValueError(f"Insufficient patterns extracted: {patterns_extracted}")

            

            # 2. _턴 분석"

            logger.info("Step 2: Analyzing patterns")

            insights = self.pattern_analyzer.analyze_patterns(min_samples=10)

            

            # 3. _략 최적"
            logger.info("Step 3: Optimizing strategy")

            optimized_strategy = self.strategy_optimizer.optimize_strategy(

                strategy_name=strategy_name,

                min_profit_threshold=2.0

            )

            

            # _션 "
            logger.info(f"Learning cycle completed successfully: {patterns_extracted} patterns, "

                       f"win rate {insights.win_rate}%")

            return result

            

        except Exception as e:

            logger.error(f"Error in learning cycle: {e}")

            session.end_time = datetime.utcnow()

            session.status = 'failed'

            session.error_message = str(e)

            self.db.commit()

            

            return {

                'session_id': session.id,

                'status': 'failed',

                'error': str(e)

            }

    

    def run_pattern_analysis_only(

        self,

        symbol: Optional[str] = None

    ) -> Dict[str, Any]:

        """?�턴 분석�??�행"""

        

        session = LearningSession(

            session_type='pattern_analysis',

            start_time=datetime.utcnow(),

            status='running',

            created_at=datetime.utcnow()

        )

        self.db.add(session)

        self.db.commit()

        

        try:

            logger.info(f"Running pattern analysis for {symbol or 'all symbols'}")

            

            insights = self.pattern_analyzer.analyze_patterns(symbol=symbol, min_samples=5)

            statistics = self.pattern_analyzer.get_pattern_statistics(symbol=symbol)

            

            session.end_time = datetime.utcnow()

            session.status = 'completed'

            session.trades_analyzed = insights.total_patterns

            session.insights = {

                'win_rate': insights.win_rate,

                'recommendations': insights.recommendations,

                'statistics': statistics

            }

            self.db.commit()

            

            return {

                'session_id': session.id,

                'status': 'success',

                'insights': insights.dict(),

                'statistics': statistics

            }

            

        except Exception as e:

            logger.error(f"Error in pattern analysis: {e}")

            session.end_time = datetime.utcnow()

            session.status = 'failed'

            session.error_message = str(e)

            self.db.commit()

            

            return {

                'session_id': session.id,

                'status': 'failed',

                'error': str(e)

            }

    

    def get_learning_history(self, limit: int = 10) -> list:

        """?�습 ?�스?�리 조회"""

        sessions = self.db.query(LearningSession).order_by(

            LearningSession.created_at.desc()

        ).limit(limit).all()

        

        return [

            {

                'id': s.id,

                'session_type': s.session_type,

                'start_time': s.start_time.isoformat(),

                'end_time': s.end_time.isoformat() if s.end_time else None,

                'status': s.status,

                'trades_analyzed': s.trades_analyzed,

                'patterns_extracted': s.patterns_extracted,

                'insights': s.insights

            }

            for s in sessions

        ]

