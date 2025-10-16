"""

Trade Pattern Analyzer - 거래 _턴 분석 "
"""

import logging

from datetime import datetime, timedelta

from typing import List, Dict, Any, Optional, Tuple

from sqlalchemy.orm import Session

from sqlalchemy import func, and_



from models.trade_history import TradeHistory

from models.ml_models import TradePattern, TradePatternCreate, PatternInsights



logger = logging.getLogger(__name__)





class PatternAnalyzer:

    """거래 ?�턴 분석�?""

    

    def __init__(self, db: Session):

        self.db = db

    

    def extract_patterns_from_trades(

        self,

        start_date: Optional[datetime] = None,

        end_date: Optional[datetime] = None,

        symbols: Optional[List[str]] = None

    ) -> int:

        """

        거래 _역"
        """

        try:

            # 거래 _역 조회

            query = self.db.query(TradeHistory)

            

            if start_date:

                query = query.filter(TradeHistory.executed_at >= start_date)

            if end_date:

                query = query.filter(TradeHistory.executed_at <= end_date)

            if symbols:

                query = query.filter(TradeHistory.symbol.in_(symbols))

            

            # "
            logger.info(f"Extracted {patterns_created} patterns from trades")

            return patterns_created

            

        except Exception as e:

            logger.error(f"Error extracting patterns: {e}")

            self.db.rollback()

            raise

    

    def _create_pattern_from_trade_pair(

        self,

        buy_trade: TradeHistory,

        sell_trade: TradeHistory

    ) -> Optional[TradePattern]:

        """매수-매도 ?�에???�턴 ?�성"""

        try:

            # _익�"
            logger.error(f"Error creating pattern: {e}")

            return None

    

    def _determine_market_condition(self, profit_loss: float) -> str:

        """?�장 ?�황 ?�단"""

        if profit_loss > 5.0:

            return 'bullish'

        elif profit_loss < -5.0:

            return 'bearish'

        else:

            return 'neutral'

    

    def analyze_patterns(

        self,

        pattern_type: Optional[str] = None,

        symbol: Optional[str] = None,

        min_samples: int = 10

    ) -> PatternInsights:

        """

        _턴 분석 �"
        """

        try:

            query = self.db.query(TradePattern)

            

            if pattern_type:

                query = query.filter(TradePattern.pattern_type == pattern_type)

            if symbol:

                query = query.filter(TradePattern.symbol == symbol)

            

            patterns = query.all()

            

            if len(patterns) < min_samples:

                logger.warning(f"Insufficient patterns: {len(patterns)} < {min_samples}")

                return self._empty_insights()

            

            # _계 계산

            winning = [p for p in patterns if p.pattern_type == 'winning']

            losing = [p for p in patterns if p.pattern_type == 'losing']

            

            total = len(patterns)

            win_count = len(winning)

            loss_count = len(losing)

            win_rate = win_count / total if total > 0 else 0.0

            

            avg_win = sum(p.profit_loss_percent for p in winning) / len(winning) if winning else 0.0

            avg_loss = sum(p.profit_loss_percent for p in losing) / len(losing) if losing else 0.0

            

            # 최적 진입 "
            logger.info(f"Pattern analysis completed: {total} patterns, {win_rate*100:.1f}% win rate")

            return insights

            

        except Exception as e:

            logger.error(f"Error analyzing patterns: {e}")

            return self._empty_insights()

    

    def _find_optimal_range(self, values: List[float]) -> Tuple[float, float]:

        """최적 �?범위 찾기 (?�균 ± ?��??�차)"""

        if not values:

            return (0.0, 100.0)

        

        import statistics

        mean = statistics.mean(values)

        stdev = statistics.stdev(values) if len(values) > 1 else 0.0

        

        return (

            round(max(0, mean - stdev), 1),

            round(min(100, mean + stdev), 1)

        )

    

    def _generate_recommendations(

        self,

        patterns: List[TradePattern],

        win_rate: float,

        avg_win: float,

        avg_loss: float,

        best_entry_range: Tuple[float, float],

        optimal_holding: float

    ) -> List[str]:

        """추천?�항 ?�성"""

        recommendations = []

        

        if win_rate < 0.4:

            recommendations.append("?�률????��?�다. 진입 조건?????�격?�게 ?�정?�세??")

        elif win_rate > 0.6:

            recommendations.append("좋�? ?�률???��??�고 ?�습?�다.")

        

        if abs(avg_loss) > avg_win * 1.5:

            recommendations.append("?�실 규모가 ?�니?? ?�절매�? ??빠르�??�행?�세??")

        

        recommendations.append(

            f"최적 진입 ?�호 ?�수: {best_entry_range[0]}-{best_entry_range[1]}"

        )

        

        recommendations.append(

            f"권장 보유 ?�간: ??{optimal_holding:.1f}?�간"

        )

        

        # _간"
                f"가??좋�? 거래 _간"
        """�??�사?�트 반환"""

        return PatternInsights(

            total_patterns=0,

            winning_patterns=0,

            losing_patterns=0,

            avg_winning_profit=0.0,

            avg_losing_loss=0.0,

            win_rate=0.0,

            best_entry_score_range=(0.0, 100.0),

            best_sentiment_range=(0.0, 100.0),

            optimal_holding_hours=24.0,

            recommendations=["?�이?��? 부족합?�다. ??많�? 거래�??�행?�세??"]

        )

    

    def get_pattern_statistics(self, symbol: Optional[str] = None) -> Dict[str, Any]:

        """?�턴 ?�계 조회"""

        try:

            query = self.db.query(TradePattern)

            if symbol:

                query = query.filter(TradePattern.symbol == symbol)

            

            total = query.count()

            winning = query.filter(TradePattern.pattern_type == 'winning').count()

            losing = query.filter(TradePattern.pattern_type == 'losing').count()

            neutral = query.filter(TradePattern.pattern_type == 'neutral').count()

            

            avg_profit = self.db.query(func.avg(TradePattern.profit_loss_percent)).filter(

                TradePattern.pattern_type == 'winning'

            ).scalar() or 0.0

            

            avg_loss = self.db.query(func.avg(TradePattern.profit_loss_percent)).filter(

                TradePattern.pattern_type == 'losing'

            ).scalar() or 0.0

            

            return {

                'total_patterns': total,

                'winning_patterns': winning,

                'losing_patterns': losing,

                'neutral_patterns': neutral,

                'win_rate': round(winning / total * 100, 2) if total > 0 else 0.0,

                'avg_winning_profit': round(avg_profit, 2),

                'avg_losing_loss': round(avg_loss, 2),

                'profit_factor': round(abs(avg_profit / avg_loss), 2) if avg_loss != 0 else 0.0

            }

            

        except Exception as e:

            logger.error(f"Error getting pattern statistics: {e}")

            return {}

