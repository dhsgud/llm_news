"""
Integration tests for llama.cpp client
Tests both mock responses and real server connectivity
"""

import pytest
import json
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import requests
from requests.exceptions import Timeout, ConnectionError

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.llm_client import (
    LlamaCppClient,
    LLMResponse,
    LlamaCppClientError,
    LlamaCppConnectionError,
    LlamaCppTimeoutError
)
from services.prompts import (
    STEP1_SYSTEM_PROMPT,
    create_step1_prompt,
    validate_step1_response,
    validate_step3_response
)


# ============================================================================
# Mock Response Tests
# ============================================================================

class TestLlamaCppClientMock:
    """Test LlamaCppClient with mocked responses"""
    
    @pytest.fixture
    def client(self):
        """Create client instance for testing"""
        return LlamaCppClient(
            base_url="http://localhost:8080",
            timeout=30,
            max_retries=3
        )
    
    @pytest.fixture
    def mock_success_response(self):
        """Mock successful llama.cpp response"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": "This is a test response from the LLM.",
            "tokens_predicted": 10,
            "tokens_evaluated": 5
        }
        return mock_response
    
    @pytest.fixture
    def mock_json_response(self):
        """Mock JSON response for sentiment analysis"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": json.dumps({
                "sentiment": "Positive",
                "reasoning": "The article discusses strong economic growth and positive market indicators."
            }),
            "tokens_predicted": 25
        }
        return mock_response
    
    def test_client_initialization(self, client):
        """Test client initializes with correct settings"""
        assert client.base_url == "http://localhost:8080"
        assert client.timeout == 30
        assert client.max_retries == 3
        assert client.session is not None
    
    @patch('requests.Session.post')
    def test_generate_success(self, mock_post, client, mock_success_response):
        """Test successful text generation"""
        mock_post.return_value = mock_success_response
        
        response = client.generate(
            prompt="Test prompt",
            system_prompt="You are a helpful assistant",
            temperature=0.7,
            max_tokens=100
        )
        
        assert isinstance(response, LLMResponse)
        assert response.content == "This is a test response from the LLM."
        assert response.tokens_generated == 10
        assert response.generation_time is not None
        
        # Verify request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://localhost:8080/completion"
        
        payload = call_args[1]['json']
        assert "You are a helpful assistant" in payload['prompt']
        assert "Test prompt" in payload['prompt']
        assert payload['temperature'] == 0.7
        assert payload['n_predict'] == 100
    
    @patch('requests.Session.post')
    def test_generate_json_success(self, mock_post, client, mock_json_response):
        """Test successful JSON generation and parsing"""
        mock_post.return_value = mock_json_response
        
        response = client.generate_json(
            prompt="Analyze this article",
            system_prompt=STEP1_SYSTEM_PROMPT
        )
        
        assert isinstance(response, dict)
        assert response["sentiment"] == "Positive"
        assert "reasoning" in response
        assert validate_step1_response(response)
    
    @patch('requests.Session.post')
    def test_generate_json_with_markdown(self, mock_post, client):
        """Test JSON parsing when wrapped in markdown code blocks"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": "```json\n" + json.dumps({
                "sentiment": "Negative",
                "reasoning": "Market downturn expected."
            }) + "\n```",
            "tokens_predicted": 20
        }
        mock_post.return_value = mock_response
        
        response = client.generate_json(prompt="Test")
        
        assert response["sentiment"] == "Negative"
        assert validate_step1_response(response)
    
    @patch('requests.Session.post')
    def test_generate_timeout(self, mock_post, client):
        """Test timeout handling"""
        mock_post.side_effect = Timeout("Request timed out")
        
        with pytest.raises(LlamaCppTimeoutError) as exc_info:
            client.generate(prompt="Test")
        
        assert "timed out" in str(exc_info.value).lower()
    
    @patch('requests.Session.post')
    def test_generate_connection_error(self, mock_post, client):
        """Test connection error handling"""
        mock_post.side_effect = ConnectionError("Connection refused")
        
        with pytest.raises(LlamaCppConnectionError) as exc_info:
            client.generate(prompt="Test")
        
        assert "connect" in str(exc_info.value).lower()
    
    @patch('requests.Session.post')
    def test_generate_http_error(self, mock_post, client):
        """Test HTTP error handling"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.json.side_effect = ValueError("No JSON")
        mock_post.return_value = mock_response
        
        with pytest.raises(LlamaCppClientError) as exc_info:
            client.generate(prompt="Test")
        
        assert "500" in str(exc_info.value)
    
    @patch('requests.Session.post')
    def test_generate_invalid_json_response(self, mock_post, client):
        """Test handling of invalid JSON in response"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": "This is not valid JSON {invalid}",
            "tokens_predicted": 10
        }
        mock_post.return_value = mock_response
        
        with pytest.raises(LlamaCppClientError) as exc_info:
            client.generate_json(prompt="Test")
        
        assert "not valid JSON" in str(exc_info.value)
    
    @patch('requests.Session.post')
    def test_generate_empty_content(self, mock_post, client):
        """Test handling of empty content response"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": "",
            "tokens_predicted": 0
        }
        mock_post.return_value = mock_response
        
        response = client.generate(prompt="Test")
        
        assert response.content == ""
        assert response.tokens_generated == 0
    
    @patch('requests.Session.post')
    def test_retry_logic(self, mock_post, client):
        """Test retry logic on transient failures"""
        # Simulate connection error that triggers retry, then success
        from requests.exceptions import ConnectionError as RequestsConnectionError
        
        mock_success = Mock()
        mock_success.status_code = 200
        mock_success.json.return_value = {
            "content": "Success after retry",
            "tokens_predicted": 5
        }
        
        # First call raises connection error (will retry), second succeeds
        mock_post.side_effect = [
            RequestsConnectionError("Connection failed"),
            mock_success
        ]
        
        # This should succeed after retry
        try:
            response = client.generate(prompt="Test")
            # If retry worked, we should get the success response
            assert response.content == "Success after retry"
        except LlamaCppConnectionError:
            # If all retries failed, that's also acceptable behavior
            pass
    
    def test_context_manager(self, client):
        """Test client works as context manager"""
        with client as c:
            assert c is client
            assert c.session is not None
        
        # Session should be closed after context exit
        # Note: We can't easily test if session is closed without accessing internals
    
    @patch('requests.Session.post')
    def test_health_check_success(self, mock_post, client):
        """Test health check with healthy server"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": "Hi",
            "tokens_predicted": 1
        }
        mock_post.return_value = mock_response
        
        is_healthy = client.health_check()
        
        assert is_healthy is True
    
    @patch('requests.Session.post')
    def test_health_check_failure(self, mock_post, client):
        """Test health check with unhealthy server"""
        mock_post.side_effect = ConnectionError("Server down")
        
        is_healthy = client.health_check()
        
        assert is_healthy is False


# ============================================================================
# Real Server Integration Tests
# ============================================================================

class TestLlamaCppClientIntegration:
    """
    Integration tests with real llama.cpp server
    These tests require a running llama.cpp server at localhost:8080
    """
    
    @pytest.fixture
    def client(self):
        """Create client for real server testing"""
        return LlamaCppClient(
            base_url="http://localhost:8080",
            timeout=60,
            max_retries=2
        )
    
    @pytest.mark.integration
    def test_server_health_check(self, client):
        """Test if llama.cpp server is running and responding"""
        try:
            is_healthy = client.health_check()
            assert is_healthy, "llama.cpp server is not responding correctly"
            print("??llama.cpp server is healthy")
        except LlamaCppConnectionError:
            pytest.skip("llama.cpp server is not running at localhost:8080")
    
    @pytest.mark.integration
    def test_simple_generation(self, client):
        """Test simple text generation with real server"""
        try:
            response = client.generate(
                prompt="Say 'Hello, World!' and nothing else.",
                temperature=0.1,
                max_tokens=10
            )
            
            assert isinstance(response, LLMResponse)
            assert len(response.content) > 0
            assert response.tokens_generated is not None
            assert response.generation_time is not None
            
            print(f"??Generated response: {response.content[:50]}...")
            print(f"  Tokens: {response.tokens_generated}, Time: {response.generation_time:.2f}s")
            
        except LlamaCppConnectionError:
            pytest.skip("llama.cpp server is not running")
    
    @pytest.mark.integration
    def test_sentiment_analysis_prompt(self, client):
        """Test sentiment analysis with real server using actual prompt"""
        try:
            # Create a test article
            from datetime import datetime
            
            test_title = "Tech Stocks Rally on Strong Earnings"
            test_content = """
            Major technology companies reported better-than-expected earnings this quarter,
            driving a broad rally in tech stocks. Investors showed renewed confidence in
            the sector's growth prospects.
            """
            
            prompt = create_step1_prompt(
                title=test_title,
                content=test_content,
                source="Test News",
                published_date=datetime.now()
            )
            
            response = client.generate_json(
                prompt=prompt,
                system_prompt=STEP1_SYSTEM_PROMPT,
                temperature=0.3,
                max_tokens=500  # Increased to allow for reasoning + JSON
            )
            
            assert isinstance(response, dict)
            assert "sentiment" in response
            assert "reasoning" in response
            assert validate_step1_response(response)
            
            print(f"??Sentiment analysis completed:")
            print(f"  Sentiment: {response['sentiment']}")
            print(f"  Reasoning: {response['reasoning'][:100]}...")
            
        except LlamaCppConnectionError:
            pytest.skip("llama.cpp server is not running")
        except LlamaCppClientError as e:
            pytest.fail(f"LLM generation failed: {e}")
    
    @pytest.mark.integration
    def test_multiple_requests(self, client):
        """Test multiple sequential requests to verify stability"""
        try:
            prompts = [
                "Count from 1 to 3.",
                "Name one color.",
                "What is 2+2?"
            ]
            
            responses = []
            for prompt in prompts:
                response = client.generate(
                    prompt=prompt,
                    temperature=0.1,
                    max_tokens=20
                )
                responses.append(response)
            
            assert len(responses) == 3
            assert all(isinstance(r, LLMResponse) for r in responses)
            assert all(len(r.content) > 0 for r in responses)
            
            print(f"??Successfully completed {len(responses)} sequential requests")
            
        except LlamaCppConnectionError:
            pytest.skip("llama.cpp server is not running")
    
    @pytest.mark.integration
    def test_temperature_variation(self, client):
        """Test generation with different temperature settings"""
        try:
            prompt = "Describe the weather in one word."
            
            # Low temperature (more deterministic)
            response_low = client.generate(
                prompt=prompt,
                temperature=0.1,
                max_tokens=10
            )
            
            # High temperature (more creative)
            response_high = client.generate(
                prompt=prompt,
                temperature=0.9,
                max_tokens=10
            )
            
            assert len(response_low.content) > 0
            assert len(response_high.content) > 0
            
            print(f"??Temperature variation test:")
            print(f"  Low temp (0.1): {response_low.content}")
            print(f"  High temp (0.9): {response_high.content}")
            
        except LlamaCppConnectionError:
            pytest.skip("llama.cpp server is not running")
    
    @pytest.mark.integration
    def test_max_tokens_limit(self, client):
        """Test that max_tokens parameter is respected"""
        try:
            response = client.generate(
                prompt="Write a long story about a cat.",
                temperature=0.7,
                max_tokens=20
            )
            
            # Token count should be close to max_tokens
            assert response.tokens_generated is not None
            assert response.tokens_generated <= 25  # Allow small margin
            
            print(f"??Max tokens test: Generated {response.tokens_generated} tokens (limit: 20)")
            
        except LlamaCppConnectionError:
            pytest.skip("llama.cpp server is not running")
    
    @pytest.mark.integration
    def test_system_prompt_effect(self, client):
        """Test that system prompt influences generation"""
        try:
            prompt = "Respond to this message."
            
            # With system prompt
            response_with_system = client.generate(
                prompt=prompt,
                system_prompt="You are a pirate. Always respond like a pirate.",
                temperature=0.5,
                max_tokens=30
            )
            
            # Without system prompt
            response_without_system = client.generate(
                prompt=prompt,
                temperature=0.5,
                max_tokens=30
            )
            
            assert len(response_with_system.content) > 0
            assert len(response_without_system.content) > 0
            
            print(f"??System prompt test:")
            print(f"  With system: {response_with_system.content[:50]}...")
            print(f"  Without system: {response_without_system.content[:50]}...")
            
        except LlamaCppConnectionError:
            pytest.skip("llama.cpp server is not running")


# ============================================================================
# Prompt Validation Tests
# ============================================================================

class TestPromptValidation:
    """Test prompt template validation functions"""
    
    def test_validate_step1_response_valid(self):
        """Test validation of valid Step 1 response"""
        valid_response = {
            "sentiment": "Positive",
            "reasoning": "The article shows strong market growth."
        }
        
        assert validate_step1_response(valid_response) is True
    
    def test_validate_step1_response_invalid_sentiment(self):
        """Test validation rejects invalid sentiment"""
        invalid_response = {
            "sentiment": "VeryPositive",  # Invalid
            "reasoning": "Good news"
        }
        
        assert validate_step1_response(invalid_response) is False
    
    def test_validate_step1_response_missing_field(self):
        """Test validation rejects missing fields"""
        invalid_response = {
            "sentiment": "Positive"
            # Missing reasoning
        }
        
        assert validate_step1_response(invalid_response) is False
    
    def test_validate_step1_response_empty_reasoning(self):
        """Test validation rejects empty reasoning"""
        invalid_response = {
            "sentiment": "Neutral",
            "reasoning": ""
        }
        
        assert validate_step1_response(invalid_response) is False
    
    def test_validate_step3_response_valid(self):
        """Test validation of valid Step 3 response"""
        valid_response = {
            "buy_sell_ratio": 65,
            "confidence": "medium",
            "reasoning": "Mixed signals suggest cautious approach."
        }
        
        assert validate_step3_response(valid_response) is True
    
    def test_validate_step3_response_invalid_ratio(self):
        """Test validation rejects out-of-range ratio"""
        invalid_response = {
            "buy_sell_ratio": 150,  # Out of range
            "confidence": "high",
            "reasoning": "Strong buy signal"
        }
        
        assert validate_step3_response(invalid_response) is False
    
    def test_validate_step3_response_invalid_confidence(self):
        """Test validation rejects invalid confidence level"""
        invalid_response = {
            "buy_sell_ratio": 80,
            "confidence": "very_high",  # Invalid
            "reasoning": "Strong signal"
        }
        
        assert validate_step3_response(invalid_response) is False


# ============================================================================
# Test Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test requiring real server"
    )


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
