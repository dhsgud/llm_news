"""
Standalone integration tests for llama.cpp client
Can be run without installing all dependencies
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 70)
print("llama.cpp Client Integration Tests (Standalone)")
print("=" * 70)

# Test 1: Import test
print("\n[Test 1] Testing imports...")
try:
    from services.llm_client import (
        LlamaCppClient,
        LLMResponse,
        LlamaCppClientError,
        LlamaCppConnectionError,
        LlamaCppTimeoutError
    )
    print("??Successfully imported llm_client module")
except ImportError as e:
    print(f"??Failed to import: {e}")
    print("  Note: This is expected if dependencies are not installed")
    print("  Install with: pip install -r requirements.txt")
    sys.exit(1)

# Test 2: Prompt validation
print("\n[Test 2] Testing prompt validation...")
try:
    from services.prompts import (
        validate_step1_response,
        validate_step3_response,
        STEP1_SYSTEM_PROMPT,
        create_step1_prompt
    )
    
    # Test valid Step 1 response
    valid_step1 = {
        "sentiment": "Positive",
        "reasoning": "Strong market growth indicators"
    }
    assert validate_step1_response(valid_step1), "Valid Step 1 response should pass"
    
    # Test invalid Step 1 response
    invalid_step1 = {
        "sentiment": "VeryPositive",
        "reasoning": "Good"
    }
    assert not validate_step1_response(invalid_step1), "Invalid Step 1 response should fail"
    
    # Test valid Step 3 response
    valid_step3 = {
        "buy_sell_ratio": 75,
        "confidence": "high",
        "reasoning": "Strong buy signals"
    }
    assert validate_step3_response(valid_step3), "Valid Step 3 response should pass"
    
    # Test invalid Step 3 response (out of range)
    invalid_step3 = {
        "buy_sell_ratio": 150,
        "confidence": "high",
        "reasoning": "Too high"
    }
    assert not validate_step3_response(invalid_step3), "Invalid Step 3 response should fail"
    
    print("??All prompt validation tests passed")
    
except AssertionError as e:
    print(f"??Validation test failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"??Unexpected error: {e}")
    sys.exit(1)

# Test 3: Mock response handling
print("\n[Test 3] Testing mock response handling...")
try:
    from unittest.mock import Mock, patch
    import json
    
    with patch('requests.Session.post') as mock_post:
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": "Test response from LLM",
            "tokens_predicted": 15,
            "tokens_evaluated": 10
        }
        mock_post.return_value = mock_response
        
        # Create client and test
        client = LlamaCppClient(base_url="http://localhost:8080", timeout=30)
        response = client.generate(prompt="Test prompt", temperature=0.7, max_tokens=100)
        
        assert isinstance(response, LLMResponse), "Response should be LLMResponse instance"
        assert response.content == "Test response from LLM", "Content should match"
        assert response.tokens_generated == 15, "Token count should match"
        assert response.generation_time is not None, "Generation time should be set"
        
    print("??Mock response handling test passed")
    
except Exception as e:
    print(f"??Mock test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: JSON parsing
print("\n[Test 4] Testing JSON response parsing...")
try:
    with patch('requests.Session.post') as mock_post:
        # Test normal JSON
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": json.dumps({
                "sentiment": "Positive",
                "reasoning": "Good market conditions"
            }),
            "tokens_predicted": 20
        }
        mock_post.return_value = mock_response
        
        client = LlamaCppClient()
        response = client.generate_json(prompt="Analyze this")
        
        assert response["sentiment"] == "Positive", "Sentiment should be Positive"
        assert "reasoning" in response, "Reasoning should be present"
        
    # Test markdown-wrapped JSON
    with patch('requests.Session.post') as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": "```json\n" + json.dumps({
                "sentiment": "Negative",
                "reasoning": "Market decline"
            }) + "\n```",
            "tokens_predicted": 18
        }
        mock_post.return_value = mock_response
        
        client = LlamaCppClient()
        response = client.generate_json(prompt="Analyze this")
        
        assert response["sentiment"] == "Negative", "Sentiment should be Negative"
        
    print("??JSON parsing tests passed")
    
except Exception as e:
    print(f"??JSON parsing test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Error handling
print("\n[Test 5] Testing error handling...")
try:
    from requests.exceptions import Timeout, ConnectionError as RequestsConnectionError
    
    # Test timeout
    with patch('requests.Session.post') as mock_post:
        mock_post.side_effect = Timeout("Request timed out")
        
        client = LlamaCppClient()
        try:
            client.generate(prompt="Test")
            assert False, "Should have raised LlamaCppTimeoutError"
        except LlamaCppTimeoutError:
            pass  # Expected
    
    # Test connection error
    with patch('requests.Session.post') as mock_post:
        mock_post.side_effect = RequestsConnectionError("Connection refused")
        
        client = LlamaCppClient()
        try:
            client.generate(prompt="Test")
            assert False, "Should have raised LlamaCppConnectionError"
        except LlamaCppConnectionError:
            pass  # Expected
    
    # Test HTTP error
    with patch('requests.Session.post') as mock_post:
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.json.side_effect = ValueError()
        mock_post.return_value = mock_response
        
        client = LlamaCppClient()
        try:
            client.generate(prompt="Test")
            assert False, "Should have raised LlamaCppClientError"
        except LlamaCppClientError as e:
            assert "500" in str(e), "Error should mention status code"
    
    print("??Error handling tests passed")
    
except Exception as e:
    print(f"??Error handling test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Server connectivity (optional)
print("\n[Test 6] Testing real server connectivity (optional)...")
try:
    client = LlamaCppClient(base_url="http://localhost:8080", timeout=5)
    print(f"  Attempting to connect to {client.base_url}...")
    
    is_healthy = client.health_check()
    
    if is_healthy:
        print("??llama.cpp server is running and healthy!")
        print("  You can run full integration tests with:")
        print("  pytest tests/test_llm_client.py -m integration -v -s")
        
        # Try a simple generation
        print("\n  Testing simple generation...")
        response = client.generate(
            prompt="Say 'Hello' and nothing else.",
            temperature=0.1,
            max_tokens=5
        )
        print(f"  Response: {response.content}")
        print(f"  Tokens: {response.tokens_generated}, Time: {response.generation_time:.2f}s")
        
    else:
        print("??llama.cpp server responded but health check failed")
        
except LlamaCppConnectionError:
    print("??llama.cpp server is not running (this is OK for mock tests)")
    print("  To test with real server:")
    print("  1. Start llama.cpp server:")
    print("     ./server -m models/Apriel-1.5-15b-Thinker-Q8_0.gguf -c 4096 --port 8080")
    print("  2. Run this test again")
except Exception as e:
    print(f"??Could not connect to server: {e}")
    print("  (This is OK - server connection is optional for mock tests)")

# Summary
print("\n" + "=" * 70)
print("Test Summary")
print("=" * 70)
print("??All mock tests passed successfully!")
print("\nThe llama.cpp client is working correctly with mocked responses.")
print("\nNext steps:")
print("1. Install dependencies: pip install -r requirements.txt")
print("2. Start llama.cpp server for integration tests")
print("3. Run full test suite: pytest tests/test_llm_client.py -v")
print("=" * 70)
