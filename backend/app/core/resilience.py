import asyncio
import time
from functools import wraps
from typing import Callable, TypeVar, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import structlog

logger = structlog.get_logger()

T = TypeVar("T")


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        expected_exception: type = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time: float = 0
        self.state = "closed"  # closed, open, half-open
    
    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        if self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half-open"
                logger.info("circuit_breaker_half_open", function=func.__name__)
            else:
                raise Exception(f"Circuit breaker open for {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
                logger.info("circuit_breaker_closed", function=func.__name__)
            return result
        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.warning("circuit_breaker_opened", function=func.__name__, failures=self.failure_count)
            raise


def async_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    exceptions: tuple = (Exception,),
):
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            @retry(
                stop=stop_after_attempt(max_attempts),
                wait=wait_exponential(multiplier=base_delay, max=max_delay),
                retry=retry_if_exception_type(exceptions),
                reraise=True,
            )
            async def retry_func():
                return await func(*args, **kwargs)
            return await retry_func()
        return wrapper
    return decorator


def with_timeout(timeout_seconds: float):
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout_seconds)
            except asyncio.TimeoutError:
                logger.error("operation_timeout", function=func.__name__, timeout=timeout_seconds)
                raise
        return wrapper
    return decorator


class GracefulDegradation:
    @staticmethod
    async def with_fallback(
        primary: Callable[..., T],
        fallback: Callable[..., T],
        *args,
        **kwargs,
    ) -> T:
        try:
            return await primary(*args, **kwargs)
        except Exception as e:
            logger.warning("primary_failed_using_fallback", primary=primary.__name__, fallback=fallback.__name__, error=str(e))
            return await fallback(*args, **kwargs)
    
    @staticmethod
    def with_default(default_value: T, func: Callable[..., T], *args, **kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.warning("function_failed_returning_default", function=func.__name__, error=str(e))
            return default_value


ollama_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
anthropic_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
openai_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)