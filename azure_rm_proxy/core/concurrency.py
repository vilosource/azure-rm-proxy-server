import asyncio
from abc import ABC, abstractmethod

import logging

logger = logging.getLogger(__name__)


class ConcurrencyLimiter:
    """Limits the number of concurrent operations using a semaphore."""

    def __init__(self, max_concurrent: int):
        """Initialize the concurrency limiter.

        Args:
            max_concurrent: Maximum number of concurrent operations allowed.
        """
        self._sem = asyncio.BoundedSemaphore(max_concurrent)
        logger.info(
            f"ConcurrencyLimiter initialized with max_concurrent={max_concurrent}"
        )

    async def __aenter__(self):
        """Acquire the semaphore when entering the context."""
        await self._sem.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release the semaphore when exiting the context."""
        self._sem.release()
