import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from azure_rm_proxy.core.concurrency import ConcurrencyLimiter


class TestConcurrencyLimiter:
    """Test suite for concurrency limiting functionality."""

    def test_init(self):
        """Test initialization of ConcurrencyLimiter."""
        # Act
        limiter = ConcurrencyLimiter(5)

        # Assert
        assert limiter._sem._value == 5
        assert limiter._sem._bound_value == 5

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test ConcurrencyLimiter as a context manager."""
        # Arrange
        limiter = ConcurrencyLimiter(3)

        # Create a proper mock that mimics real semaphore behavior
        # The real asyncio.BoundedSemaphore has acquire() that returns a coroutine
        # but release() that returns None
        mock_sem = MagicMock()
        mock_sem.acquire = AsyncMock()
        # Regular MagicMock for release since it doesn't return a coroutine
        mock_sem.release = MagicMock()

        limiter._sem = mock_sem

        # Act
        async with limiter:
            # Intentionally empty - this test only verifies that 
            # the context manager correctly acquires and releases the semaphore
            pass

        # Assert
        mock_sem.acquire.assert_awaited_once()
        mock_sem.release.assert_called_once()

    @pytest.mark.asyncio
    async def test_concurrent_operations_limited(self):
        """Test that operations are properly limited."""
        # Arrange
        max_concurrent = 2
        limiter = ConcurrencyLimiter(max_concurrent)

        # Create a counter to track concurrent operations
        counter = 0
        max_counter = 0

        async def operation(delay):
            nonlocal counter, max_counter
            async with limiter:
                counter += 1
                max_counter = max(counter, max_counter)
                await asyncio.sleep(delay)
                counter -= 1

        # Act
        # Start 5 operations with different delays
        tasks = [
            asyncio.create_task(operation(0.1)),
            asyncio.create_task(operation(0.2)),
            asyncio.create_task(operation(0.1)),
            asyncio.create_task(operation(0.2)),
            asyncio.create_task(operation(0.1)),
        ]

        await asyncio.gather(*tasks)

        # Assert
        assert max_counter <= max_concurrent
