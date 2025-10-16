"""
Example: Signal Generation Integration

This example demonstrates how to use the signal generation module
with sentiment analysis results to calculate buy/sell signals.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
from services.signal_generator import (
    SentimentQuantifier,
    VIXFetcher,
    SignalCalculator
)


def example_basic_usage():
    """Basic usage of signal generation components"""
    print("=" * 60)
    print("Example 1: Basic Signal Generation")
    print("=" * 60)
    
    # Initialize calculator
    calculator = SignalCalculator()
    
    # Simulate sentiment data from the past week
    base_date = datetime.now()
    sentiment_data = [
        {"sentiment": "Positive", "analyzed_at": base_date},
        {"sentiment": "Positive", "analyzed_at": base_date - timedelta(days=1)},
        {"sentiment": "Negative", "analyzed_at": base_date - timedelta(days=2)},
        {"sentiment": "Neutral", "analyzed_at": base_date - timedelta(days=3)},
        {"sentiment": "Positive", "analyzed_at": base_date - timedelta(days=4)},
        {"sentiment": "Negative", "analyzed_at": base_date - timedelta(days=5)},
        {"sentiment": "Neutral", "analyzed_at": base_date - timedelta(days=6)},
    ]
    
    # Calculate buy/sell ratio
    result = calculator.calculate_buy_sell_ratio(sentiment_data)
    
    print(f"\n?�� Buy/Sell Ratio: {result['ratio']}")
    print(f"?�� Interpretation: {result['interpretation']}")
    print(f"?�� Raw Signal Score: {result['signal_score']:.2f}")
    print(f"?�� VIX (normalized): {result['vix_normalized']:.3f}")
    print(f"\n?�� Daily Scores:")
    for date, score in sorted(result['daily_scores'].items()):
        emoji = "?��" if score > 0 else "?��" if score < 0 else "??
        print(f"  {emoji} {date}: {score:+.2f}")


def example_conservative_bias():
    """Demonstrate conservative bias with negative sentiment"""
    print("\n" + "=" * 60)
    print("Example 2: Conservative Bias (Negative Sentiment)")
    print("=" * 60)
    
    quantifier = SentimentQuantifier()
    
    print("\n?�� Sentiment Quantification:")
    print(f"  Positive: {quantifier.quantify('Positive'):+.1f}")
    print(f"  Neutral:  {quantifier.quantify('Neutral'):+.1f}")
    print(f"  Negative: {quantifier.quantify('Negative'):+.1f} (1.5x weight)")
    
    # Compare balanced vs negative-heavy scenarios
    base_date = datetime.now()
    
    balanced_data = [
        {"sentiment": "Positive", "analyzed_at": base_date},
        {"sentiment": "Negative", "analyzed_at": base_date},
    ]
    
    negative_heavy_data = [
        {"sentiment": "Positive", "analyzed_at": base_date},
        {"sentiment": "Negative", "analyzed_at": base_date},
        {"sentiment": "Negative", "analyzed_at": base_date},
    ]
    
    calculator = SignalCalculator()
    
    balanced_result = calculator.calculate_buy_sell_ratio(balanced_data)
    negative_result = calculator.calculate_buy_sell_ratio(negative_heavy_data)
    
    print(f"\n?�️  Balanced (1 Pos, 1 Neg):")
    print(f"  Ratio: {balanced_result['ratio']} - {balanced_result['interpretation']}")
    
    print(f"\n?�️  Negative-Heavy (1 Pos, 2 Neg):")
    print(f"  Ratio: {negative_result['ratio']} - {negative_result['interpretation']}")
    print(f"  Note: Conservative bias makes system more cautious with negative news")


def example_vix_impact():
    """Demonstrate VIX impact on signal calculation"""
    print("\n" + "=" * 60)
    print("Example 3: VIX Impact on Signals")
    print("=" * 60)
    
    base_date = datetime.now()
    sentiment_data = [
        {"sentiment": "Positive", "analyzed_at": base_date},
        {"sentiment": "Positive", "analyzed_at": base_date - timedelta(days=1)},
        {"sentiment": "Positive", "analyzed_at": base_date - timedelta(days=2)},
    ]
    
    calculator = SignalCalculator()
    
    # Low VIX (calm market)
    low_vix = 0.1
    result_low = calculator.calculate_buy_sell_ratio(sentiment_data, vix_normalized=low_vix)
    
    # High VIX (volatile market)
    high_vix = 0.8
    result_high = calculator.calculate_buy_sell_ratio(sentiment_data, vix_normalized=high_vix)
    
    print(f"\n?�� Low VIX (Calm Market, VIX={low_vix}):")
    print(f"  Ratio: {result_low['ratio']} - {result_low['interpretation']}")
    print(f"  Signal: {result_low['signal_score']:.2f}")
    
    print(f"\n?�� High VIX (Volatile Market, VIX={high_vix}):")
    print(f"  Ratio: {result_high['ratio']} - {result_high['interpretation']}")
    print(f"  Signal: {result_high['signal_score']:.2f}")
    print(f"\n  Note: Higher VIX amplifies sentiment impact")


def example_normalization_methods():
    """Compare sigmoid vs linear normalization"""
    print("\n" + "=" * 60)
    print("Example 4: Normalization Methods Comparison")
    print("=" * 60)
    
    base_date = datetime.now()
    sentiment_data = [
        {"sentiment": "Positive", "analyzed_at": base_date - timedelta(days=i)}
        for i in range(7)
    ]
    
    calculator = SignalCalculator()
    
    sigmoid_result = calculator.calculate_buy_sell_ratio(
        sentiment_data, 
        normalization_method="sigmoid"
    )
    
    linear_result = calculator.calculate_buy_sell_ratio(
        sentiment_data,
        normalization_method="linear"
    )
    
    print(f"\n?�� Sigmoid Normalization:")
    print(f"  Ratio: {sigmoid_result['ratio']} - {sigmoid_result['interpretation']}")
    
    print(f"\n?�� Linear Normalization:")
    print(f"  Ratio: {linear_result['ratio']} - {linear_result['interpretation']}")
    
    print(f"\n  Note: Sigmoid provides smoother transitions, linear is more predictable")


def example_real_world_scenario():
    """Simulate a real-world market scenario"""
    print("\n" + "=" * 60)
    print("Example 5: Real-World Market Scenario")
    print("=" * 60)
    
    # Simulate: Market starts positive, then negative news hits
    base_date = datetime.now()
    sentiment_data = [
        # Recent days - negative news
        {"sentiment": "Negative", "analyzed_at": base_date},
        {"sentiment": "Negative", "analyzed_at": base_date - timedelta(days=1)},
        {"sentiment": "Negative", "analyzed_at": base_date - timedelta(days=2)},
        # Earlier days - positive
        {"sentiment": "Positive", "analyzed_at": base_date - timedelta(days=3)},
        {"sentiment": "Positive", "analyzed_at": base_date - timedelta(days=4)},
        {"sentiment": "Neutral", "analyzed_at": base_date - timedelta(days=5)},
        {"sentiment": "Positive", "analyzed_at": base_date - timedelta(days=6)},
    ]
    
    calculator = SignalCalculator()
    result = calculator.calculate_buy_sell_ratio(sentiment_data)
    
    print("\n?�� Scenario: Market turned negative in recent days")
    print(f"\n?�� Analysis Result:")
    print(f"  Buy/Sell Ratio: {result['ratio']}")
    print(f"  Interpretation: {result['interpretation']}")
    print(f"  Signal Score: {result['signal_score']:.2f}")
    
    print(f"\n?�� Weekly Sentiment Trend:")
    for date, score in sorted(result['daily_scores'].items(), reverse=True):
        emoji = "?��" if score > 0 else "?��" if score < 0 else "??
        bar = "?? * int(abs(score) * 10)
        print(f"  {emoji} {date}: {score:+.2f} {bar}")
    
    print(f"\n?�� Recommendation:")
    if result['ratio'] <= 30:
        print("  ?�️  Strong Sell signal - Consider reducing positions")
    elif result['ratio'] <= 70:
        print("  ?�️  Neutral signal - Hold current positions")
    else:
        print("  ??Strong Buy signal - Consider increasing positions")


if __name__ == "__main__":
    print("\n?? Signal Generation Module Examples\n")
    
    example_basic_usage()
    example_conservative_bias()
    example_vix_impact()
    example_normalization_methods()
    example_real_world_scenario()
    
    print("\n" + "=" * 60)
    print("??All examples completed successfully!")
    print("=" * 60 + "\n")
