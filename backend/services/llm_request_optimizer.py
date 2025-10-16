"""
LLM Request Optimizer Module
Handles batch processing and request queuing for LLM inference optimization
"""

import asyncio
import logging
import time
from typing import List, Optional, Dict, Any, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from queue import PriorityQueue, Empty
from threading import Thread, Lock
import uuid

try:
    from services.llm_client import LlamaCppClient, LlamaCppClientError, LLMResponse
except ImportError:
    from services.llm_client import LlamaCppClient, LlamaCppClientError, LLMResponse

logger = logging.getLogger(__name__)


class RequestPriority(Enum):
    """Priority levels for LLM requests"""
    LOW = 3
    NORMAL = 2
    HIGH = 1
    CRITICAL = 0


@dataclass
class LLMRequest:
    """
    Represents a single LLM request in the queue
    """
    request_id: str
    prompt: str
    system_prompt: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    priority: RequestPriority = RequestPriority.NORMAL
    callback: Optional[Callable] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    # Result fields (populated after processing)
    response: Optional[LLMResponse] = None
    error: Optional[Exception] = None
    completed_at: Optional[datetime] = None
    
    def __lt__(self, other):
        """Compare by priority for PriorityQueue"""
        return self.priority.value < other.priority.value


@dataclass
class BatchRequest:
    """
    Represents a batch of LLM requests to be processed together
    """
    batch_id: str
    requests: List[LLMRequest]
    created_at: datetime = field(default_factory=datetime.now)
    
    def __len__(self):
        return len(self.requests)


class LLMRequestQueue:
    """
    Thread-safe priority queue for LLM requests
    
    Manages incoming requests with priority-based ordering
    and provides batch retrieval capabilities.
    """
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize request queue
        
        Args:
            max_size: Maximum queue size (0 = unlimited)
        """
        self.queue = PriorityQueue(maxsize=max_size)
        self.pending_requests: Dict[str, LLMRequest] = {}
        self.lock = Lock()
        
        logger.info(f"LLMRequestQueue initialized with max_size={max_size}")
    
    def enqueue(self, request: LLMRequest) -> str:
        """
        Add request to queue
        
        Args:
            request: LLMRequest to enqueue
            
        Returns:
            Request ID
            
        Raises:
            ValueError: If queue is full
        """
        try:
            self.queue.put(request, block=False)
            
            with self.lock:
                self.pending_requests[request.request_id] = request
            
            logger.debug(
                f"Enqueued request {request.request_id} "
                f"with priority {request.priority.name}"
            )
            
            return request.request_id
            
        except Exception as e:
            logger.error(f"Failed to enqueue request: {e}")
            raise ValueError(f"Queue is full or error occurred: {e}")
    
    def dequeue(self, timeout: Optional[float] = None) -> Optional[LLMRequest]:
        """
        Remove and return highest priority request
        
        Args:
            timeout: Maximum time to wait for request (None = block indefinitely)
            
        Returns:
            LLMRequest or None if timeout
        """
        try:
            request = self.queue.get(timeout=timeout)
            logger.debug(f"Dequeued request {request.request_id}")
            return request
            
        except Empty:
            return None
    
    def dequeue_batch(
        self,
        batch_size: int,
        timeout: Optional[float] = 1.0
    ) -> List[LLMRequest]:
        """
        Dequeue multiple requests for batch processing
        
        Args:
            batch_size: Maximum number of requests to dequeue
            timeout: Timeout for waiting for first request
            
        Returns:
            List of LLMRequest objects (may be less than batch_size)
        """
        requests = []
        
        # Get first request with timeout
        first_request = self.dequeue(timeout=timeout)
        if first_request:
            requests.append(first_request)
        
        # Get remaining requests without blocking
        for _ in range(batch_size - 1):
            request = self.dequeue(timeout=0.01)
            if request:
                requests.append(request)
            else:
                break
        
        if requests:
            logger.debug(f"Dequeued batch of {len(requests)} requests")
        
        return requests
    
    def mark_completed(self, request_id: str):
        """
        Mark request as completed and remove from pending
        
        Args:
            request_id: ID of completed request
        """
        with self.lock:
            if request_id in self.pending_requests:
                del self.pending_requests[request_id]
                logger.debug(f"Marked request {request_id} as completed")
    
    def get_request(self, request_id: str) -> Optional[LLMRequest]:
        """
        Get request by ID
        
        Args:
            request_id: Request ID
            
        Returns:
            LLMRequest or None if not found
        """
        with self.lock:
            return self.pending_requests.get(request_id)
    
    def size(self) -> int:
        """Get current queue size"""
        return self.queue.qsize()
    
    def is_empty(self) -> bool:
        """Check if queue is empty"""
        return self.queue.empty()


class LLMBatchProcessor:
    """
    Processes LLM requests in batches for improved efficiency
    
    Batching strategies:
    1. Time-based: Process batch after timeout
    2. Size-based: Process batch when size threshold reached
    3. Priority-based: Process high-priority requests immediately
    """
    
    def __init__(
        self,
        llama_client: Optional[LlamaCppClient] = None,
        batch_size: int = 5,
        batch_timeout: float = 2.0,
        max_concurrent_batches: int = 2
    ):
        """
        Initialize batch processor
        
        Args:
            llama_client: LlamaCppClient instance
            batch_size: Maximum requests per batch
            batch_timeout: Maximum time to wait for batch to fill (seconds)
            max_concurrent_batches: Maximum number of concurrent batch processes
        """
        self.llama_client = llama_client or LlamaCppClient()
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.max_concurrent_batches = max_concurrent_batches
        
        self.queue = LLMRequestQueue()
        self.is_running = False
        self.worker_thread: Optional[Thread] = None
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "total_batches": 0,
            "total_errors": 0,
            "average_batch_size": 0.0,
            "average_processing_time": 0.0
        }
        self.stats_lock = Lock()
        
        logger.info(
            f"LLMBatchProcessor initialized: batch_size={batch_size}, "
            f"batch_timeout={batch_timeout}s"
        )
    
    def start(self):
        """Start the batch processing worker thread"""
        if self.is_running:
            logger.warning("Batch processor already running")
            return
        
        self.is_running = True
        self.worker_thread = Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        
        logger.info("Batch processor started")
    
    def stop(self):
        """Stop the batch processing worker thread"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.worker_thread:
            self.worker_thread.join(timeout=5.0)
        
        logger.info("Batch processor stopped")
    
    def submit_request(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        priority: RequestPriority = RequestPriority.NORMAL,
        callback: Optional[Callable] = None
    ) -> str:
        """
        Submit a request for batch processing
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: LLM temperature
            max_tokens: Maximum tokens to generate
            priority: Request priority
            callback: Optional callback function(request: LLMRequest)
            
        Returns:
            Request ID for tracking
        """
        request = LLMRequest(
            request_id=str(uuid.uuid4()),
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            priority=priority,
            callback=callback
        )
        
        request_id = self.queue.enqueue(request)
        
        with self.stats_lock:
            self.stats["total_requests"] += 1
        
        logger.debug(f"Submitted request {request_id} for batch processing")
        
        return request_id
    
    def get_result(
        self,
        request_id: str,
        timeout: Optional[float] = None
    ) -> Optional[LLMResponse]:
        """
        Get result for a submitted request
        
        Blocks until result is available or timeout.
        
        Args:
            request_id: Request ID
            timeout: Maximum time to wait (None = wait indefinitely)
            
        Returns:
            LLMResponse or None if timeout/error
            
        Raises:
            LlamaCppClientError: If request failed
        """
        start_time = time.time()
        
        while True:
            request = self.queue.get_request(request_id)
            
            if request is None:
                # Request not found (might be completed and removed)
                logger.warning(f"Request {request_id} not found")
                return None
            
            if request.response is not None:
                return request.response
            
            if request.error is not None:
                raise request.error
            
            # Check timeout
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    logger.warning(f"Timeout waiting for request {request_id}")
                    return None
            
            # Wait a bit before checking again
            time.sleep(0.1)
    
    def _worker_loop(self):
        """
        Main worker loop for batch processing
        
        Continuously dequeues requests and processes them in batches.
        """
        logger.info("Batch processor worker loop started")
        
        while self.is_running:
            try:
                # Dequeue a batch of requests
                requests = self.queue.dequeue_batch(
                    batch_size=self.batch_size,
                    timeout=self.batch_timeout
                )
                
                if not requests:
                    continue
                
                # Process the batch
                self._process_batch(requests)
                
            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)
                time.sleep(1.0)  # Back off on error
        
        logger.info("Batch processor worker loop stopped")
    
    def _process_batch(self, requests: List[LLMRequest]):
        """
        Process a batch of requests
        
        Processes requests sequentially but with optimized batching.
        Future enhancement: True parallel processing with multiple LLM instances.
        
        Args:
            requests: List of LLMRequest objects to process
        """
        batch_id = str(uuid.uuid4())[:8]
        batch_start = time.time()
        
        logger.info(f"Processing batch {batch_id} with {len(requests)} requests")
        
        successful = 0
        failed = 0
        
        for request in requests:
            try:
                # Process individual request
                response = self.llama_client.generate(
                    prompt=request.prompt,
                    system_prompt=request.system_prompt,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens
                )
                
                # Store result
                request.response = response
                request.completed_at = datetime.now()
                successful += 1
                
                # Call callback if provided
                if request.callback:
                    try:
                        request.callback(request)
                    except Exception as e:
                        logger.error(f"Callback error for request {request.request_id}: {e}")
                
            except Exception as e:
                logger.error(f"Failed to process request {request.request_id}: {e}")
                request.error = e
                request.completed_at = datetime.now()
                failed += 1
            
            finally:
                # Mark as completed
                self.queue.mark_completed(request.request_id)
        
        batch_time = time.time() - batch_start
        
        # Update statistics
        with self.stats_lock:
            self.stats["total_batches"] += 1
            self.stats["total_errors"] += failed
            
            # Update running averages
            total_batches = self.stats["total_batches"]
            self.stats["average_batch_size"] = (
                (self.stats["average_batch_size"] * (total_batches - 1) + len(requests))
                / total_batches
            )
            self.stats["average_processing_time"] = (
                (self.stats["average_processing_time"] * (total_batches - 1) + batch_time)
                / total_batches
            )
        
        logger.info(
            f"Batch {batch_id} completed: {successful} successful, {failed} failed, "
            f"{batch_time:.2f}s total"
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get processing statistics
        
        Returns:
            Dictionary with statistics
        """
        with self.stats_lock:
            return self.stats.copy()
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        return self.queue.size()


class LLMRequestOptimizer:
    """
    High-level interface for optimized LLM request handling
    
    Provides both synchronous and asynchronous interfaces for:
    - Batch processing
    - Request queuing
    - Priority management
    - Performance monitoring
    """
    
    def __init__(
        self,
        llama_client: Optional[LlamaCppClient] = None,
        enable_batching: bool = True,
        batch_size: int = 5,
        batch_timeout: float = 2.0
    ):
        """
        Initialize request optimizer
        
        Args:
            llama_client: LlamaCppClient instance
            enable_batching: Enable batch processing
            batch_size: Maximum requests per batch
            batch_timeout: Batch timeout in seconds
        """
        self.llama_client = llama_client or LlamaCppClient()
        self.enable_batching = enable_batching
        
        if enable_batching:
            self.batch_processor = LLMBatchProcessor(
                llama_client=self.llama_client,
                batch_size=batch_size,
                batch_timeout=batch_timeout
            )
            self.batch_processor.start()
        else:
            self.batch_processor = None
        
        logger.info(
            f"LLMRequestOptimizer initialized: batching={'enabled' if enable_batching else 'disabled'}"
        )
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        priority: RequestPriority = RequestPriority.NORMAL,
        use_batching: bool = True
    ) -> LLMResponse:
        """
        Generate LLM response with optimization
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: LLM temperature
            max_tokens: Maximum tokens
            priority: Request priority
            use_batching: Use batch processing if enabled
            
        Returns:
            LLMResponse
        """
        # Use batch processing if enabled and requested
        if self.enable_batching and use_batching and self.batch_processor:
            request_id = self.batch_processor.submit_request(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                priority=priority
            )
            
            # Wait for result
            response = self.batch_processor.get_result(request_id, timeout=120.0)
            
            if response is None:
                raise LlamaCppClientError("Request timed out or failed")
            
            return response
        
        # Direct processing without batching
        return self.llama_client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        priority: RequestPriority = RequestPriority.NORMAL,
        use_batching: bool = True
    ) -> Dict[str, Any]:
        """
        Generate JSON response with optimization
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: LLM temperature
            max_tokens: Maximum tokens
            priority: Request priority
            use_batching: Use batch processing
            
        Returns:
            Parsed JSON dictionary
        """
        response = self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            priority=priority,
            use_batching=use_batching
        )
        
        # Parse JSON from response
        import json
        content = response.content.strip()
        
        # Handle markdown code blocks
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            if end != -1:
                content = content[start:end].strip()
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            if end != -1:
                content = content[start:end].strip()
        
        # Extract JSON object
        if "{" in content:
            start = content.find("{")
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
        
        return json.loads(content)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get optimization statistics"""
        if self.batch_processor:
            return self.batch_processor.get_stats()
        return {}
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        if self.batch_processor:
            return self.batch_processor.get_queue_size()
        return 0
    
    def close(self):
        """Close optimizer and cleanup resources"""
        if self.batch_processor:
            self.batch_processor.stop()
        
        if self.llama_client:
            self.llama_client.close()
        
        logger.info("LLMRequestOptimizer closed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
