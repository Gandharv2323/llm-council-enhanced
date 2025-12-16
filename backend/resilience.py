"""
Fault tolerance and resilience for LLM Council.
Handles timeouts, retries, and partial failures gracefully.
"""

import asyncio
import time
import hashlib
from typing import Optional, Any, TypeVar, Callable
from functools import wraps
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ModelQueryError(Exception):
    """Error querying a model"""
    def __init__(self, model: str, message: str, recoverable: bool = True):
        self.model = model
        self.message = message
        self.recoverable = recoverable
        super().__init__(f"{model}: {message}")


class InsufficientResponsesError(Exception):
    """Not enough models responded successfully"""
    def __init__(self, required: int, received: int, errors: list[str]):
        self.required = required
        self.received = received
        self.errors = errors
        super().__init__(f"Need {required} responses, got {received}")


async def with_timeout(
    coro,
    timeout_seconds: float,
    error_message: str = "Operation timed out"
) -> Any:
    """Execute coroutine with timeout"""
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        raise ModelQueryError("unknown", error_message, recoverable=True)


async def with_retry(
    coro_factory: Callable[[], Any],
    max_retries: int = 2,
    base_delay: float = 1.0,
    exponential: bool = True
) -> Any:
    """Execute coroutine with retry logic"""
    last_error = None
    
    for attempt in range(max_retries + 1):
        try:
            return await coro_factory()
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt if exponential else 1)
                logger.warning(f"Retry {attempt + 1}/{max_retries} after {delay}s: {e}")
                await asyncio.sleep(delay)
    
    raise last_error


async def resilient_parallel_query(
    query_func: Callable[[str], Any],
    models: list[str],
    min_required: int = 2,
    timeout_per_model: float = 30.0,
    allow_partial: bool = True
) -> tuple[list[Any], list[str]]:
    """
    Query multiple models with fault tolerance.
    
    Returns:
        - List of successful responses
        - List of failed model names
    """
    async def query_with_timeout(model: str):
        try:
            return await asyncio.wait_for(
                query_func(model),
                timeout=timeout_per_model
            )
        except asyncio.TimeoutError:
            raise ModelQueryError(model, "Timeout", recoverable=True)
        except Exception as e:
            raise ModelQueryError(model, str(e), recoverable=False)
    
    tasks = [query_with_timeout(m) for m in models]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    successful = []
    failed = []
    errors = []
    
    for model, result in zip(models, results):
        if isinstance(result, Exception):
            failed.append(model)
            errors.append(str(result))
            logger.error(f"Model {model} failed: {result}")
        else:
            successful.append(result)
    
    if len(successful) < min_required:
        if not allow_partial:
            raise InsufficientResponsesError(min_required, len(successful), errors)
        logger.warning(f"Only {len(successful)}/{min_required} models succeeded")
    
    return successful, failed


class QueryCache:
    """In-memory cache for query results with TTL"""
    
    def __init__(self, ttl_seconds: int = 3600):
        self.cache: dict[str, tuple[Any, float]] = {}
        self.ttl = ttl_seconds
    
    def _cache_key(self, query: str, model: str) -> str:
        return hashlib.sha256(f"{model}:{query}".encode()).hexdigest()[:32]
    
    def get(self, query: str, model: str) -> Optional[Any]:
        key = self._cache_key(query, model)
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                logger.debug(f"Cache hit for {model}")
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, query: str, model: str, value: Any):
        key = self._cache_key(query, model)
        self.cache[key] = (value, time.time())
    
    def clear(self):
        self.cache.clear()
    
    def clear_expired(self):
        now = time.time()
        expired = [k for k, (_, ts) in self.cache.items() if now - ts >= self.ttl]
        for k in expired:
            del self.cache[k]


class CircuitBreaker:
    """Circuit breaker pattern for model endpoints"""
    
    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: float = 60.0
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures: dict[str, int] = {}
        self.open_until: dict[str, float] = {}
    
    def is_open(self, model: str) -> bool:
        """Check if circuit is open (blocking requests)"""
        if model in self.open_until:
            if time.time() >= self.open_until[model]:
                # Recovery period over, half-open state
                del self.open_until[model]
                self.failures[model] = 0
                return False
            return True
        return False
    
    def record_success(self, model: str):
        """Record successful request"""
        self.failures[model] = 0
    
    def record_failure(self, model: str):
        """Record failed request"""
        self.failures[model] = self.failures.get(model, 0) + 1
        if self.failures[model] >= self.failure_threshold:
            self.open_until[model] = time.time() + self.recovery_timeout
            logger.warning(f"Circuit opened for {model}")
    
    def get_available_models(self, models: list[str]) -> list[str]:
        """Filter out models with open circuits"""
        return [m for m in models if not self.is_open(m)]


# Global instances
_cache = QueryCache()
_circuit_breaker = CircuitBreaker()


def get_cache() -> QueryCache:
    return _cache


def get_circuit_breaker() -> CircuitBreaker:
    return _circuit_breaker
