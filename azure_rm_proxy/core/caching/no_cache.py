"""No-op cache implementation."""

import logging
from typing import Any, Optional

from .base_cache import BaseCache

logger = logging.getLogger(__name__)


class NoCache(BaseCache):
    """A no-op cache implementation that doesn't actually cache anything."""

    def __init__(self):
        """Initialize the no-op cache."""
        logger.info("Initialized no-op cache (caching disabled)")

    def get(self, key: str) -> Optional[Any]:
        """
        Always returns None as if the key was not found.

        Args:
            key: The cache key

        Returns:
            Always None
        """
        logger.debug(f"No-op cache get for {key} (always returns None)")
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        No-op implementation of set.

        Args:
            key: The cache key
            value: The value to cache
            ttl: Optional time to live in seconds
        """
        logger.debug(f"No-op cache set for {key} (does nothing)")

    def set_with_ttl(self, key: str, value: Any, ttl: int) -> None:
        """
        No-op implementation of set_with_ttl.

        Args:
            key: The cache key
            value: The value to cache
            ttl: Time to live in seconds
        """
        logger.debug(
            f"No-op cache set_with_ttl for {key} with TTL {ttl} (does nothing)"
        )

    def delete(self, key: str) -> None:
        """
        No-op implementation of delete.

        Args:
            key: The cache key
        """
        logger.debug(f"No-op cache delete for {key} (does nothing)")

    def clear(self) -> None:
        """No-op implementation of clear."""
        logger.debug("No-op cache clear (does nothing)")
