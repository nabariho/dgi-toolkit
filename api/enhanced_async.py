"""Enhanced async error handling with timeouts, retries, and resilience patterns.

This module provides robust async operations with comprehensive error handling,
timeout management, retry logic, and circuit breaker patterns for enterprise-grade
reliability.
"""

import asyncio
import logging
import time
from collections.abc import Callable
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, TypeVar

from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryStrategy(str, Enum):
    """Retry strategy enumeration."""

    FIXED = "fixed"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    JITTER = "jitter"


class CircuitState(str, Enum):
    """Circuit breaker state enumeration."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class AsyncOperationConfig(BaseModel):
    """Configuration for async operations."""

    timeout_seconds: float = 30.0
    max_retries: int = 3
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    base_delay: float = 1.0
    max_delay: float = 60.0
    jitter: bool = True
    circuit_breaker_enabled: bool = True
    circuit_failure_threshold: int = 5
    circuit_recovery_timeout: float = 60.0


class AsyncOperationResult(BaseModel):
    """Result of an async operation with metadata."""

    success: bool
    result: Any = None
    error: str | None = None
    attempts: int = 1
    total_duration: float = 0.0
    circuit_state: CircuitState = CircuitState.CLOSED


class CircuitBreaker:
    """Circuit breaker implementation for resilient async operations."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        name: str = "default",
    ) -> None:
        """Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time to wait before trying half-open
            name: Circuit breaker name for logging
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.name = name

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: datetime | None = None
        self.success_count = 0

    def can_execute(self) -> bool:
        """Check if operation can be executed."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if (
                self.last_failure_time
                and datetime.now() - self.last_failure_time
                > timedelta(seconds=self.recovery_timeout)
            ):
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                logger.info(f"Circuit breaker '{self.name}' transitioned to HALF_OPEN")
                return True
            return False

        # HALF_OPEN state
        return True

    def record_success(self) -> None:
        """Record a successful operation."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            # After first success in half-open, close the circuit
            if self.success_count >= 1:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                logger.info(f"Circuit breaker '{self.name}' transitioned to CLOSED")
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0

    def record_failure(self) -> None:
        """Record a failed operation."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if (
            self.state == CircuitState.CLOSED
            and self.failure_count >= self.failure_threshold
        ):
            self.state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker '{self.name}' opened after {self.failure_count} failures"
            )
        elif self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker '{self.name}' reopened after failure in half-open state"
            )


class RetryManager:
    """Manager for retry logic with different strategies."""

    @staticmethod
    def calculate_delay(
        attempt: int,
        base_delay: float,
        max_delay: float,
        strategy: RetryStrategy,
        jitter: bool = True,
    ) -> float:
        """Calculate delay before next retry attempt.

        Args:
            attempt: Current attempt number (0-based)
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
            strategy: Retry strategy to use
            jitter: Whether to add jitter to prevent thundering herd

        Returns:
            Delay in seconds
        """
        import random

        if strategy == RetryStrategy.FIXED:
            delay = base_delay
        elif strategy == RetryStrategy.LINEAR:
            delay = base_delay * (attempt + 1)
        elif strategy == RetryStrategy.EXPONENTIAL:
            delay = base_delay * (2**attempt)
        elif strategy == RetryStrategy.JITTER:
            delay = base_delay + random.uniform(0, base_delay)
        else:
            delay = base_delay

        # Apply maximum delay limit
        delay = min(delay, max_delay)

        # Add jitter if enabled
        if jitter and strategy != RetryStrategy.JITTER:
            jitter_amount = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_amount, jitter_amount)

        return max(0, delay)


class EnhancedAsyncExecutor:
    """Enhanced async executor with comprehensive error handling."""

    def __init__(self, config: AsyncOperationConfig | None = None) -> None:
        """Initialize async executor.

        Args:
            config: Configuration for async operations
        """
        self.config = config or AsyncOperationConfig()
        self.circuit_breakers: dict[str, CircuitBreaker] = {}

    def get_circuit_breaker(self, name: str) -> CircuitBreaker:
        """Get or create a circuit breaker for a named operation.

        Args:
            name: Operation name for circuit breaker

        Returns:
            CircuitBreaker instance
        """
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(
                failure_threshold=self.config.circuit_failure_threshold,
                recovery_timeout=self.config.circuit_recovery_timeout,
                name=name,
            )
        return self.circuit_breakers[name]

    async def execute_with_retry(
        self,
        operation: Callable[[], T],
        operation_name: str = "async_operation",
        config: AsyncOperationConfig | None = None,
    ) -> AsyncOperationResult:
        """Execute an async operation with retry logic and circuit breaker.

        Args:
            operation: Async operation to execute
            operation_name: Name for logging and circuit breaker
            config: Override configuration for this operation

        Returns:
            AsyncOperationResult with success status and metadata
        """
        op_config = config or self.config
        circuit_breaker = self.get_circuit_breaker(operation_name)
        start_time = time.time()

        # Check circuit breaker
        if op_config.circuit_breaker_enabled and not circuit_breaker.can_execute():
            return AsyncOperationResult(
                success=False,
                error=f"Circuit breaker '{operation_name}' is OPEN",
                attempts=0,
                total_duration=0.0,
                circuit_state=circuit_breaker.state,
            )

        last_exception = None

        for attempt in range(op_config.max_retries + 1):
            try:
                # Execute with timeout
                result = await asyncio.wait_for(
                    operation(), timeout=op_config.timeout_seconds
                )

                # Record success
                if op_config.circuit_breaker_enabled:
                    circuit_breaker.record_success()

                total_duration = time.time() - start_time

                logger.info(
                    f"Operation '{operation_name}' succeeded on attempt {attempt + 1} "
                    f"after {total_duration:.2f}s"
                )

                return AsyncOperationResult(
                    success=True,
                    result=result,
                    attempts=attempt + 1,
                    total_duration=total_duration,
                    circuit_state=circuit_breaker.state,
                )

            except TimeoutError:
                last_exception = (
                    f"Operation timed out after {op_config.timeout_seconds}s"
                )
                logger.warning(
                    f"Operation '{operation_name}' timed out on attempt {attempt + 1}"
                )

            except asyncio.CancelledError:
                logger.info(f"Operation '{operation_name}' was cancelled")
                raise

            except Exception as e:
                last_exception = str(e)
                logger.warning(
                    f"Operation '{operation_name}' failed on attempt {attempt + 1}: {e}"
                )

            # Record failure for circuit breaker
            if op_config.circuit_breaker_enabled:
                circuit_breaker.record_failure()

            # Calculate delay before retry (skip for last attempt)
            if attempt < op_config.max_retries:
                delay = RetryManager.calculate_delay(
                    attempt=attempt,
                    base_delay=op_config.base_delay,
                    max_delay=op_config.max_delay,
                    strategy=op_config.retry_strategy,
                    jitter=op_config.jitter,
                )

                logger.info(
                    f"Retrying operation '{operation_name}' in {delay:.2f}s "
                    f"(attempt {attempt + 2}/{op_config.max_retries + 1})"
                )

                await asyncio.sleep(delay)

        total_duration = time.time() - start_time

        logger.error(
            f"Operation '{operation_name}' failed after {op_config.max_retries + 1} attempts "
            f"in {total_duration:.2f}s. Last error: {last_exception}"
        )

        return AsyncOperationResult(
            success=False,
            error=last_exception,
            attempts=op_config.max_retries + 1,
            total_duration=total_duration,
            circuit_state=circuit_breaker.state,
        )

    async def execute_with_timeout(
        self,
        operation: Callable[[], T],
        timeout_seconds: float,
        operation_name: str = "async_operation",
    ) -> T:
        """Execute an async operation with timeout.

        Args:
            operation: Async operation to execute
            timeout_seconds: Timeout in seconds
            operation_name: Name for logging

        Returns:
            Operation result

        Raises:
            asyncio.TimeoutError: If operation times out
        """
        try:
            result = await asyncio.wait_for(operation(), timeout=timeout_seconds)
            logger.debug(f"Operation '{operation_name}' completed within timeout")
            return result
        except TimeoutError:
            logger.error(
                f"Operation '{operation_name}' timed out after {timeout_seconds}s"
            )
            raise

    async def gather_with_error_handling(
        self,
        *operations: Callable[[], T],
        return_exceptions: bool = True,
        timeout_seconds: float | None = None,
    ) -> list[T | Exception]:
        """Gather multiple async operations with error handling.

        Args:
            *operations: Async operations to execute concurrently
            return_exceptions: Whether to return exceptions instead of raising
            timeout_seconds: Optional timeout for the entire gather operation

        Returns:
            List of results or exceptions
        """
        tasks = [asyncio.create_task(op()) for op in operations]

        try:
            if timeout_seconds:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=return_exceptions),
                    timeout=timeout_seconds,
                )
            else:
                results = await asyncio.gather(
                    *tasks, return_exceptions=return_exceptions
                )

            return results

        except TimeoutError:
            # Cancel all tasks if gather times out
            for task in tasks:
                task.cancel()

            # Wait for tasks to acknowledge cancellation
            await asyncio.gather(*tasks, return_exceptions=True)
            raise

    def get_circuit_breaker_stats(self) -> dict[str, dict[str, Any]]:
        """Get statistics for all circuit breakers.

        Returns:
            Dictionary with circuit breaker statistics
        """
        stats = {}
        for name, breaker in self.circuit_breakers.items():
            stats[name] = {
                "state": breaker.state.value,
                "failure_count": breaker.failure_count,
                "success_count": breaker.success_count,
                "last_failure_time": (
                    breaker.last_failure_time.isoformat()
                    if breaker.last_failure_time
                    else None
                ),
            }
        return stats


# Global instance for convenience
default_executor = EnhancedAsyncExecutor()


# Convenience functions
async def execute_with_retry(
    operation: Callable[[], T],
    operation_name: str = "async_operation",
    config: AsyncOperationConfig | None = None,
) -> AsyncOperationResult:
    """Execute an async operation with retry logic using default executor."""
    return await default_executor.execute_with_retry(operation, operation_name, config)


async def execute_with_timeout(
    operation: Callable[[], T],
    timeout_seconds: float,
    operation_name: str = "async_operation",
) -> T:
    """Execute an async operation with timeout using default executor."""
    return await default_executor.execute_with_timeout(
        operation, timeout_seconds, operation_name
    )
