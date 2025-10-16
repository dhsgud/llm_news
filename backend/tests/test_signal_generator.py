"""
Tests for signal generation module
"""

import pytest
from datetime import datetime, timedelta
from services.signal_generator import SentimentQuantifier, VIXFetcher, SignalCalculator


class TestSentimentQuantifier:
    """Test SentimentQuantifier class"""
    
    def test_quantify_positive(self):
        """Test positive sentiment quantification"""
        quantifier = SentimentQuantifier()
        score = quantifier.quantify("Positive")
        assert score == 1.0
    
    def test_quantify_negative(self):
        """Test negative sentiment quantification with conservative weight"""
        quantifier = SentimentQuantifier()
        score = quantifier.quantify("Negative")
        assert score == -1.5  # -1.0 * 1.5 weight
    
    def test_quantify_neutral(self):
        """Test neutral sentiment quantification"""
        quantifier = SentimentQuantifier()
        score = quantifier.quantify("Neutral")
        assert score == 0.0
    
    def test_quantify_case_insensitive(self):
        """Test that sentiment is case-insensitive"""
        quantifier = SentimentQuantifier()
        assert quantifier.quantify("positive") == 1.0
        assert quantifier.quantify("NEGATIVE") == -1.5
        assert quantifier.quantify("NeUtRaL") == 0.0
    
    def test_quantify_unknown(self):
        """Test unknown sentiment defaults to neutral"""
        quantifier = SentimentQuantifier()
        score = quantifier.quantify("Unknown")
        assert score == 0.0
    
    def test_calculate_daily_score(self):
        """Test daily score calculation"""
        quantifier = SentimentQuantifier()
        
        sentiment_results = [
            {"sentiment": "Positive"},
            {"sentiment": "Positive"},
            {"sentiment": "Negative"}
        ]
        
        # Expected: (1.0 + 1.0 + (-1.5)) / 3 = 0.5 / 3 = 0.167
        score = quantifier.calculate_daily_score(sentiment_results)
        assert abs(score - 0.167) < 0.01
    
    def test_calculate_daily_score_empty(self):
        """Test daily score with empty list"""
        quantifier = SentimentQuantifier()
        score = quantifier.calculate_daily_score([])
        assert score == 0.0
    
    def test_calculate_weekly_scores(self):
        """Test weekly scores calculation"""
        quantifier = SentimentQuantifier()
        
        base_date = datetime(2025, 10, 1)
        sentiment_data = [
            {"sentiment": "Positive", "analyzed_at": base_date},
            {"sentiment": "Negative", "analyzed_at": base_date},
            {"sentiment": "Positive", "analyzed_at": base_date + timedelta(days=1)},
        ]
        
        weekly_scores = quantifier.calculate_weekly_scores(sentiment_data)
        
        assert "2025-10-01" in weekly_scores
        assert "2025-10-02" in weekly_scores
        assert len(weekly_scores) == 2


class TestVIXFetcher:
    """Test VIXFetcher class"""
    
    def test_mock_vix(self):
        """Test mock VIX fetching"""
        fetcher = VIXFetcher(api_source="mock")
        vix = fetcher.get_current_vix()
        assert vix == 18.5
    
    def test_normalize_vix_low(self):
        """Test VIX normalization for low value"""
        fetcher = VIXFetcher()
        normalized = fetcher.normalize_vix(10.0)
        assert normalized == 0.0
    
    def test_normalize_vix_high(self):
        """Test VIX normalization for high value"""
        fetcher = VIXFetcher()
        normalized = fetcher.normalize_vix(40.0)
        assert normalized == 1.0
    
    def test_normalize_vix_mid(self):
        """Test VIX normalization for mid value"""
        fetcher = VIXFetcher()
        normalized = fetcher.normalize_vix(25.0)
        # (25 - 10) / (40 - 10) = 15 / 30 = 0.5
        assert abs(normalized - 0.5) < 0.01
    
    def test_normalize_vix_extreme(self):
        """Test VIX normalization clamps extreme values"""
        fetcher = VIXFetcher()
        
        # Very low VIX should clamp to 0
        normalized_low = fetcher.normalize_vix(5.0)
        assert normalized_low == 0.0
        
        # Very high VIX should clamp to 1
        normalized_high = fetcher.normalize_vix(80.0)
        assert normalized_high == 1.0
    
    def test_get_normalized_vix(self):
        """Test combined fetch and normalize"""
        fetcher = VIXFetcher(api_source="mock")
        normalized = fetcher.get_normalized_vix()
        # Mock VIX is 18.5, normalized: (18.5 - 10) / 30 = 0.283
        assert 0.2 < normalized < 0.3


class TestSignalCalculator:
    """Test SignalCalculator class"""
    
    def test_calculate_weekly_signal(self):
        """Test weekly signal calculation"""
        calculator = SignalCalculator()
        
        daily_scores = [1.0, 0.5, -1.5, 0.0, 1.0, 0.5, -0.5]
        vix_normalized = 0.3
        
        # Expected: sum(scores) * (1 + 0.3) = 1.0 * 1.3 = 1.3
        signal = calculator.calculate_weekly_signal(daily_scores, vix_normalized)
        
        # Sum of scores: 1.0 + 0.5 - 1.5 + 0.0 + 1.0 + 0.5 - 0.5 = 1.0
        # Weighted: 1.0 * 1.3 = 1.3
        assert abs(signal - 1.3) < 0.01
    
    def test_calculate_weekly_signal_empty(self):
        """Test weekly signal with empty scores"""
        calculator = SignalCalculator()
        signal = calculator.calculate_weekly_signal([])
        assert signal == 0.0
    
    def test_sigmoid(self):
        """Test sigmoid function"""
        calculator = SignalCalculator()
        
        # At center, sigmoid should be 0.5
        assert abs(calculator.sigmoid(0.0, center=0.0) - 0.5) < 0.01
        
        # Large positive should approach 1
        assert calculator.sigmoid(10.0, center=0.0) > 0.9
        
        # Large negative should approach 0
        assert calculator.sigmoid(-10.0, center=0.0) < 0.1
    
    def test_normalize_to_ratio_sigmoid(self):
        """Test ratio normalization using sigmoid"""
        calculator = SignalCalculator()
        
        # Positive signal should give high ratio
        ratio_positive = calculator.normalize_to_ratio(5.0, method="sigmoid")
        assert ratio_positive > 70
        
        # Negative signal should give low ratio
        ratio_negative = calculator.normalize_to_ratio(-5.0, method="sigmoid")
        assert ratio_negative < 30
        
        # Neutral signal should give mid ratio
        ratio_neutral = calculator.normalize_to_ratio(0.0, method="sigmoid")
        assert 40 < ratio_neutral < 60
    
    def test_normalize_to_ratio_linear(self):
        """Test ratio normalization using linear method"""
        calculator = SignalCalculator()
        
        # Test linear normalization
        ratio = calculator.normalize_to_ratio(0.0, method="linear")
        # 0 is in middle of range [-15, 10], so should be around 60
        assert 55 < ratio < 65
    
    def test_normalize_to_ratio_bounds(self):
        """Test ratio is always in valid range"""
        calculator = SignalCalculator()
        
        # Extreme values should clamp to 0-100
        ratio_extreme_high = calculator.normalize_to_ratio(1000.0)
        assert 0 <= ratio_extreme_high <= 100
        
        ratio_extreme_low = calculator.normalize_to_ratio(-1000.0)
        assert 0 <= ratio_extreme_low <= 100
    
    def test_calculate_buy_sell_ratio(self):
        """Test complete buy/sell ratio calculation"""
        calculator = SignalCalculator()
        
        base_date = datetime(2025, 10, 1)
        sentiment_data = [
            {"sentiment": "Positive", "analyzed_at": base_date},
            {"sentiment": "Positive", "analyzed_at": base_date + timedelta(days=1)},
            {"sentiment": "Positive", "analyzed_at": base_date + timedelta(days=2)},
        ]
        
        result = calculator.calculate_buy_sell_ratio(sentiment_data, vix_normalized=0.2)
        
        assert "ratio" in result
        assert "signal_score" in result
        assert "daily_scores" in result
        assert "vix_normalized" in result
        assert "interpretation" in result
        
        # All positive sentiment should give high ratio
        assert result["ratio"] > 50
        assert result["interpretation"] in ["Neutral", "Strong Buy"]
    
    def test_calculate_buy_sell_ratio_negative(self):
        """Test buy/sell ratio with negative sentiment"""
        calculator = SignalCalculator()
        
        base_date = datetime(2025, 10, 1)
        sentiment_data = [
            {"sentiment": "Negative", "analyzed_at": base_date},
            {"sentiment": "Negative", "analyzed_at": base_date + timedelta(days=1)},
            {"sentiment": "Negative", "analyzed_at": base_date + timedelta(days=2)},
        ]
        
        result = calculator.calculate_buy_sell_ratio(sentiment_data, vix_normalized=0.5)
        
        # All negative sentiment should give low ratio
        assert result["ratio"] < 50
        assert result["interpretation"] in ["Strong Sell", "Neutral"]
    
    def test_calculate_buy_sell_ratio_empty(self):
        """Test buy/sell ratio with no data"""
        calculator = SignalCalculator()
        
        result = calculator.calculate_buy_sell_ratio([])
        
        assert result["ratio"] == 50
        assert result["interpretation"] == "Neutral"


class TestSignalCalculationWithKnownInputs:
    """Test signal calculation with known inputs to verify output correctness"""
    
    def test_all_positive_sentiment_high_ratio(self):
        """Test that all positive sentiment produces high buy ratio"""
        calculator = SignalCalculator()
        
        # 7 days of positive sentiment
        base_date = datetime(2025, 10, 1)
        sentiment_data = [
            {"sentiment": "Positive", "analyzed_at": base_date + timedelta(days=i)}
            for i in range(7)
        ]
        
        # Low VIX (calm market)
        result = calculator.calculate_buy_sell_ratio(sentiment_data, vix_normalized=0.2)
        
        # Expected: 7 days * 1.0 score * 1.2 weight = 8.4
        assert abs(result["signal_score"] - 8.4) < 0.1
        assert result["ratio"] >= 71, "All positive should give Strong Buy (>70)"
        assert result["interpretation"] == "Strong Buy"
    
    def test_all_negative_sentiment_low_ratio(self):
        """Test that all negative sentiment produces low sell ratio"""
        calculator = SignalCalculator()
        
        # 7 days of negative sentiment
        base_date = datetime(2025, 10, 1)
        sentiment_data = [
            {"sentiment": "Negative", "analyzed_at": base_date + timedelta(days=i)}
            for i in range(7)
        ]
        
        # Low VIX
        result = calculator.calculate_buy_sell_ratio(sentiment_data, vix_normalized=0.2)
        
        # Expected: 7 days * -1.5 score * 1.2 weight = -12.6
        assert abs(result["signal_score"] - (-12.6)) < 0.1
        assert result["ratio"] <= 30, "All negative should give Strong Sell (<30)"
        assert result["interpretation"] == "Strong Sell"
    
    def test_mixed_sentiment_neutral_ratio(self):
        """Test that mixed sentiment produces neutral ratio"""
        calculator = SignalCalculator()
        
        base_date = datetime(2025, 10, 1)
        sentiment_data = [
            {"sentiment": "Positive", "analyzed_at": base_date},
            {"sentiment": "Positive", "analyzed_at": base_date + timedelta(days=1)},
            {"sentiment": "Negative", "analyzed_at": base_date + timedelta(days=2)},
            {"sentiment": "Neutral", "analyzed_at": base_date + timedelta(days=3)},
            {"sentiment": "Positive", "analyzed_at": base_date + timedelta(days=4)},
            {"sentiment": "Negative", "analyzed_at": base_date + timedelta(days=5)},
            {"sentiment": "Neutral", "analyzed_at": base_date + timedelta(days=6)},
        ]
        
        result = calculator.calculate_buy_sell_ratio(sentiment_data, vix_normalized=0.3)
        
        # Expected: (1.0 + 1.0 - 1.5 + 0.0 + 1.0 - 1.5 + 0.0) * 1.3 = 0.0 * 1.3 = 0.0
        assert abs(result["signal_score"]) < 0.1
        assert 31 <= result["ratio"] <= 70, "Balanced sentiment should give Neutral (31-70)"
        assert result["interpretation"] == "Neutral"
    
    def test_high_vix_amplifies_signal(self):
        """Test that high VIX amplifies the signal score"""
        calculator = SignalCalculator()
        
        base_date = datetime(2025, 10, 1)
        sentiment_data = [
            {"sentiment": "Positive", "analyzed_at": base_date + timedelta(days=i)}
            for i in range(7)
        ]
        
        # Compare low VIX vs high VIX
        result_low_vix = calculator.calculate_buy_sell_ratio(sentiment_data, vix_normalized=0.1)
        result_high_vix = calculator.calculate_buy_sell_ratio(sentiment_data, vix_normalized=0.9)
        
        # High VIX should produce higher signal score
        assert result_high_vix["signal_score"] > result_low_vix["signal_score"]
        
        # Expected low VIX: 7 * 1.0 * 1.1 = 7.7
        assert abs(result_low_vix["signal_score"] - 7.7) < 0.1
        
        # Expected high VIX: 7 * 1.0 * 1.9 = 13.3
        assert abs(result_high_vix["signal_score"] - 13.3) < 0.1


class TestConservativeWeightEffect:
    """Test that conservative weight (1.5x) is properly applied to negative sentiment"""
    
    def test_negative_weight_is_applied(self):
        """Verify negative sentiment gets 1.5x weight"""
        quantifier = SentimentQuantifier()
        
        positive_score = quantifier.quantify("Positive")
        negative_score = quantifier.quantify("Negative")
        
        # Negative should be -1.5, not -1.0
        assert positive_score == 1.0
        assert negative_score == -1.5
        assert abs(negative_score / positive_score) == 1.5
    
    def test_conservative_bias_in_mixed_sentiment(self):
        """Test that negative news has more impact than positive in mixed scenarios"""
        quantifier = SentimentQuantifier()
        
        # Scenario 1: 1 positive, 1 negative
        balanced_results = [
            {"sentiment": "Positive"},
            {"sentiment": "Negative"}
        ]
        
        score = quantifier.calculate_daily_score(balanced_results)
        
        # Expected: (1.0 + (-1.5)) / 2 = -0.5 / 2 = -0.25
        # Should be negative due to conservative weight
        assert score < 0, "Equal positive/negative should lean negative due to conservative weight"
        assert abs(score - (-0.25)) < 0.01
    
    def test_conservative_bias_in_signal_calculation(self):
        """Test conservative bias affects final signal"""
        calculator = SignalCalculator()
        
        base_date = datetime(2025, 10, 1)
        
        # Scenario: 3 positive, 2 negative (more positive articles)
        sentiment_data = [
            {"sentiment": "Positive", "analyzed_at": base_date},
            {"sentiment": "Positive", "analyzed_at": base_date + timedelta(days=1)},
            {"sentiment": "Positive", "analyzed_at": base_date + timedelta(days=2)},
            {"sentiment": "Negative", "analyzed_at": base_date + timedelta(days=3)},
            {"sentiment": "Negative", "analyzed_at": base_date + timedelta(days=4)},
        ]
        
        result = calculator.calculate_buy_sell_ratio(sentiment_data, vix_normalized=0.2)
        
        # Expected: (1.0 + 1.0 + 1.0 - 1.5 - 1.5) * 1.2 = 0.0 * 1.2 = 0.0
        # Despite more positive articles, conservative weight balances it out
        assert abs(result["signal_score"]) < 0.5
        assert result["ratio"] <= 60, "Conservative weight should prevent high ratio"
    
    def test_negative_dominance_with_conservative_weight(self):
        """Test that few negative articles can outweigh many positive ones"""
        quantifier = SentimentQuantifier()
        
        # 2 positive, 1 negative
        results = [
            {"sentiment": "Positive"},
            {"sentiment": "Positive"},
            {"sentiment": "Negative"}
        ]
        
        score = quantifier.calculate_daily_score(results)
        
        # Expected: (1.0 + 1.0 - 1.5) / 3 = 0.5 / 3 = 0.167
        # Without conservative weight, it would be (1.0 + 1.0 - 1.0) / 3 = 0.333
        assert score < 0.2, "Conservative weight reduces positive bias"
        assert abs(score - 0.167) < 0.01
    
    def test_extreme_negative_scenario(self):
        """Test extreme negative sentiment produces very low ratio"""
        calculator = SignalCalculator()
        
        base_date = datetime(2025, 10, 1)
        sentiment_data = [
            {"sentiment": "Negative", "analyzed_at": base_date + timedelta(days=i)}
            for i in range(7)
        ]
        
        # High VIX (fearful market) amplifies negative signal
        result = calculator.calculate_buy_sell_ratio(sentiment_data, vix_normalized=0.8)
        
        # Expected: 7 * -1.5 * 1.8 = -18.9
        assert result["signal_score"] < -15
        assert result["ratio"] <= 20, "Extreme negative should give very low ratio"
        assert result["interpretation"] == "Strong Sell"


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_single_day_data(self):
        """Test calculation with only one day of data"""
        calculator = SignalCalculator()
        
        sentiment_data = [
            {"sentiment": "Positive", "analyzed_at": datetime(2025, 10, 1)}
        ]
        
        result = calculator.calculate_buy_sell_ratio(sentiment_data, vix_normalized=0.3)
        
        # Expected: 1 * 1.0 * 1.3 = 1.3
        assert abs(result["signal_score"] - 1.3) < 0.1
        assert result["ratio"] > 50
    
    def test_zero_vix(self):
        """Test calculation with zero VIX (no volatility)"""
        calculator = SignalCalculator()
        
        daily_scores = [1.0, 1.0, 1.0]
        signal = calculator.calculate_weekly_signal(daily_scores, vix_normalized=0.0)
        
        # Expected: 3 * 1.0 * 1.0 = 3.0
        assert abs(signal - 3.0) < 0.01
    
    def test_max_vix(self):
        """Test calculation with maximum VIX (extreme volatility)"""
        calculator = SignalCalculator()
        
        daily_scores = [1.0, 1.0, 1.0]
        signal = calculator.calculate_weekly_signal(daily_scores, vix_normalized=1.0)
        
        # Expected: 3 * 1.0 * 2.0 = 6.0
        assert abs(signal - 6.0) < 0.01
    
    def test_all_neutral_sentiment(self):
        """Test with all neutral sentiment"""
        calculator = SignalCalculator()
        
        base_date = datetime(2025, 10, 1)
        sentiment_data = [
            {"sentiment": "Neutral", "analyzed_at": base_date + timedelta(days=i)}
            for i in range(7)
        ]
        
        result = calculator.calculate_buy_sell_ratio(sentiment_data, vix_normalized=0.5)
        
        # Expected: 7 * 0.0 * 1.5 = 0.0
        assert abs(result["signal_score"]) < 0.01
        assert 40 <= result["ratio"] <= 60, "All neutral should give mid-range ratio"
        assert result["interpretation"] == "Neutral"
    
    def test_multiple_articles_same_day(self):
        """Test handling multiple articles on the same day"""
        quantifier = SentimentQuantifier()
        
        base_date = datetime(2025, 10, 1)
        sentiment_data = [
            {"sentiment": "Positive", "analyzed_at": base_date},
            {"sentiment": "Positive", "analyzed_at": base_date},
            {"sentiment": "Negative", "analyzed_at": base_date},
            {"sentiment": "Positive", "analyzed_at": base_date + timedelta(days=1)},
        ]
        
        weekly_scores = quantifier.calculate_weekly_scores(sentiment_data)
        
        # Day 1 should have 3 articles averaged
        assert "2025-10-01" in weekly_scores
        day1_score = weekly_scores["2025-10-01"]
        
        # Expected: (1.0 + 1.0 - 1.5) / 3 = 0.167
        assert abs(day1_score - 0.167) < 0.01
        
        # Day 2 should have 1 article
        assert "2025-10-02" in weekly_scores
        assert weekly_scores["2025-10-02"] == 1.0


class TestNormalizationMethods:
    """Test different normalization methods produce valid results"""
    
    def test_sigmoid_vs_linear_comparison(self):
        """Compare sigmoid and linear normalization methods"""
        calculator = SignalCalculator()
        
        test_scores = [-10.0, -5.0, 0.0, 5.0, 10.0]
        
        for score in test_scores:
            ratio_sigmoid = calculator.normalize_to_ratio(score, method="sigmoid")
            ratio_linear = calculator.normalize_to_ratio(score, method="linear")
            
            # Both should be in valid range
            assert 0 <= ratio_sigmoid <= 100
            assert 0 <= ratio_linear <= 100
            
            # Both should agree on direction (positive score = higher ratio)
            if score > 0:
                assert ratio_sigmoid > 50
                assert ratio_linear > 50
            elif score < 0:
                assert ratio_sigmoid < 50
                assert ratio_linear < 50
    
    def test_sigmoid_smooth_transition(self):
        """Test sigmoid provides smooth transition around neutral"""
        calculator = SignalCalculator()
        
        # Test scores around neutral point
        scores = [-2.0, -1.0, 0.0, 1.0, 2.0]
        ratios = [calculator.normalize_to_ratio(s, method="sigmoid") for s in scores]
        
        # Ratios should be monotonically increasing
        for i in range(len(ratios) - 1):
            assert ratios[i] < ratios[i + 1], "Sigmoid should be monotonically increasing"
    
    def test_linear_proportional_scaling(self):
        """Test linear method provides proportional scaling"""
        calculator = SignalCalculator()
        
        # Test that doubling the score roughly doubles the distance from center
        ratio_1 = calculator.normalize_to_ratio(2.0, method="linear")
        ratio_2 = calculator.normalize_to_ratio(4.0, method="linear")
        
        # Both should be above 50 (positive)
        assert ratio_1 > 50
        assert ratio_2 > 50
        
        # Ratio_2 should be higher
        assert ratio_2 > ratio_1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
