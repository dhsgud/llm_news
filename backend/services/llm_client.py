"""
llama.cpp Client Module
Handles communication with local llama.cpp server for LLM inference
"""

import json
import logging
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from config import settings
except ImportError:
    from config import settings


logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Response from LLM inference"""
    content: str
    tokens_generated: Optional[int] = None
    generation_time: Optional[float] = None


class LlamaCppClientError(Exception):
    """Base exception for llama.cpp client errors"""
    pass


class LlamaCppConnectionError(LlamaCppClientError):
    """Raised when connection to llama.cpp server fails"""
    pass


class LlamaCppTimeoutError(LlamaCppClientError):
    """Raised when llama.cpp server request times out"""
    pass


class LlamaCppClient:
    """
    Client for communicating with llama.cpp server
    
    Handles HTTP requests to the /completion endpoint with:
    - Automatic retry logic
    - Timeout handling
    - Error recovery
    - Response parsing
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: int = 3,
        backoff_factor: float = 0.5
    ):
        """
        Initialize llama.cpp client
        
        Args:
            base_url: Base URL of llama.cpp server (default from settings)
            timeout: Request timeout in seconds (default from settings)
            max_retries: Maximum number of retry attempts
            backoff_factor: Backoff factor for exponential retry delay
        """
        self.base_url = base_url or settings.llama_cpp_base_url
        self.timeout = timeout or settings.llm_timeout
        self.max_retries = max_retries
        
        # Configure session with retry strategy
        self.session = self._create_session(max_retries, backoff_factor)
        
        logger.info(
            f"Initialized LlamaCppClient: base_url={self.base_url}, "
            f"timeout={self.timeout}s, max_retries={max_retries}"
        )
    
    def _create_session(self, max_retries: int, backoff_factor: float) -> requests.Session:
        """
        Create requests session with retry configuration
        
        Args:
            max_retries: Maximum number of retries
            backoff_factor: Backoff factor for exponential delay
            
        Returns:
            Configured requests.Session
        """
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"],
            raise_on_status=False
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop: Optional[list] = None
    ) -> LLMResponse:
        """
        Generate text completion from llama.cpp server
        
        Args:
            prompt: User prompt text
            system_prompt: Optional system prompt for context
            temperature: Sampling temperature (default from settings)
            max_tokens: Maximum tokens to generate (default from settings)
            stop: Optional list of stop sequences
            
        Returns:
            LLMResponse with generated content
            
        Raises:
            LlamaCppConnectionError: If connection fails
            LlamaCppTimeoutError: If request times out
            LlamaCppClientError: For other errors
        """
        temperature = temperature if temperature is not None else settings.llm_temperature
        max_tokens = max_tokens if max_tokens is not None else settings.llm_max_tokens
        
        # Build the full prompt with system message if provided
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        payload = {
            "prompt": full_prompt,
            "temperature": temperature,
            "n_predict": max_tokens,
            "stop": stop or [],
            "stream": False
        }
        
        logger.debug(f"Sending request to llama.cpp: temperature={temperature}, max_tokens={max_tokens}")
        
        start_time = time.time()
        
        try:
            response = self._make_request(payload)
            generation_time = time.time() - start_time
            
            # Parse response
            llm_response = self._parse_response(response, generation_time)
            
            logger.info(
                f"LLM generation completed: {llm_response.tokens_generated} tokens "
                f"in {generation_time:.2f}s"
            )
            
            # Record metrics
            try:
                from services.monitoring import get_metrics_collector
                collector = get_metrics_collector()
                collector.record_llm_inference(
                    generation_time,
                    llm_response.tokens_generated,
                    success=True
                )
            except Exception as metric_error:
                logger.debug(f"Failed to record LLM metrics: {metric_error}")
            
            return llm_response
            
        except requests.exceptions.Timeout as e:
            generation_time = time.time() - start_time
            logger.error(f"llama.cpp request timed out after {self.timeout}s: {e}")
            
            # Record failed metric
            try:
                from services.monitoring import get_metrics_collector
                collector = get_metrics_collector()
                collector.record_llm_inference(generation_time, success=False)
            except:
                pass
            
            raise LlamaCppTimeoutError(f"Request timed out after {self.timeout}s") from e
            
        except requests.exceptions.ConnectionError as e:
            generation_time = time.time() - start_time
            logger.error(f"Failed to connect to llama.cpp server at {self.base_url}: {e}")
            
            # Record failed metric
            try:
                from services.monitoring import get_metrics_collector
                collector = get_metrics_collector()
                collector.record_llm_inference(generation_time, success=False)
            except:
                pass
            
            raise LlamaCppConnectionError(
                f"Cannot connect to llama.cpp server at {self.base_url}. "
                "Ensure the server is running."
            ) from e
            
        except Exception as e:
            generation_time = time.time() - start_time
            logger.error(f"Unexpected error during LLM generation: {e}", exc_info=True)
            
            # Record failed metric
            try:
                from services.monitoring import get_metrics_collector
                collector = get_metrics_collector()
                collector.record_llm_inference(generation_time, success=False)
            except:
                pass
            
            raise LlamaCppClientError(f"LLM generation failed: {str(e)}") from e
    
    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate JSON response from llama.cpp server
        
        Convenience method that parses the response as JSON.
        Useful for structured outputs like sentiment analysis.
        
        Args:
            prompt: User prompt text (should request JSON output)
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Parsed JSON dictionary
            
        Raises:
            LlamaCppClientError: If response is not valid JSON
        """
        response = self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        try:
            # Try to extract JSON from response
            content = response.content.strip()
            
            # Handle cases where LLM wraps JSON in markdown code blocks
            if "```json" in content:
                # Extract content between ```json and ```
                start = content.find("```json") + 7
                end = content.find("```", start)
                if end != -1:
                    content = content[start:end].strip()
            elif "```" in content:
                # Extract content between ``` and ```
                start = content.find("```") + 3
                end = content.find("```", start)
                if end != -1:
                    content = content[start:end].strip()
            
            # Try to find JSON object in the response (between { and })
            # This handles cases where LLM outputs reasoning before JSON
            if "{" in content:
                start = content.find("{")
                # Find the matching closing brace
                brace_count = 0
                end = -1
                for i in range(start, len(content)):
                    if content[i] == "{":
                        brace_count += 1
                    elif content[i] == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            end = i + 1
                            break
                
                if end != -1:
                    content = content[start:end]
                else:
                    # If no matching brace found, response might be truncated
                    logger.warning("JSON response appears to be truncated")
                    # Try with rfind as fallback
                    if "}" in content:
                        end = content.rfind("}") + 1
                        content = content[start:end]
            
            return json.loads(content)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}\nResponse: {response.content}")
            raise LlamaCppClientError(
                f"LLM response is not valid JSON: {str(e)}"
            ) from e
    
    def _make_request(self, payload: Dict[str, Any]) -> requests.Response:
        """
        Make HTTP POST request to llama.cpp /completion endpoint
        
        Args:
            payload: Request payload dictionary
            
        Returns:
            Response object
            
        Raises:
            requests.exceptions.RequestException: On request failure
        """
        url = f"{self.base_url}/completion"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        response = self.session.post(
            url,
            json=payload,
            headers=headers,
            timeout=self.timeout
        )
        
        # Check for HTTP errors
        if response.status_code != 200:
            error_msg = f"llama.cpp server returned status {response.status_code}"
            try:
                error_detail = response.json()
                error_msg += f": {error_detail}"
            except:
                error_msg += f": {response.text}"
            
            logger.error(error_msg)
            raise LlamaCppClientError(error_msg)
        
        return response
    
    def _parse_response(self, response: requests.Response, generation_time: float) -> LLMResponse:
        """
        Parse llama.cpp response JSON
        
        Args:
            response: HTTP response object
            generation_time: Time taken for generation
            
        Returns:
            LLMResponse object
            
        Raises:
            LlamaCppClientError: If response format is invalid
        """
        try:
            data = response.json()
            
            # llama.cpp returns content in 'content' field
            content = data.get("content", "")
            
            if not content:
                logger.warning("llama.cpp returned empty content")
            
            tokens_generated = data.get("tokens_predicted", data.get("tokens_evaluated"))
            
            return LLMResponse(
                content=content,
                tokens_generated=tokens_generated,
                generation_time=generation_time
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse llama.cpp response: {e}")
            raise LlamaCppClientError(f"Invalid JSON response from llama.cpp: {str(e)}") from e
        except KeyError as e:
            logger.error(f"Missing expected field in llama.cpp response: {e}")
            raise LlamaCppClientError(f"Unexpected response format: {str(e)}") from e
    
    def health_check(self) -> bool:
        """
        Check if llama.cpp server is healthy and responding
        
        Returns:
            True if server is healthy, False otherwise
        """
        try:
            # Try a simple request with minimal tokens
            response = self.generate(
                prompt="Hello",
                temperature=0.1,
                max_tokens=5
            )
            return bool(response.content)
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def close(self):
        """Close the HTTP session"""
        self.session.close()
        logger.debug("LlamaCppClient session closed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
