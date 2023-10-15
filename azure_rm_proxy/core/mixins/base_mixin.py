"""Base mixin for Azure Resource Service components."""

import logging
from typing import Any, Dict, Optional
from ..caching import CacheStrategy

logger = logging.getLogger(__name__)

class BaseAzureResourceMixin:
    """Base mixin class with shared utility methods for Azure resource mixins."""
    
    def __init__(self):
        """Placeholder init method for IDE compatibility. Will not be called."""
        # This won't be called as this is a mixin, but helps with IDE autocomplete
        self.credential = None
        self.cache: Optional[CacheStrategy] = None
        self.limiter = None
        
    def _get_cache_key(self, key_components: list) -> str:
        """
        Create a standardized cache key from components.
        
        Args:
            key_components: List of strings to join for the cache key
            
        Returns:
            Standardized cache key
        """
        return ":".join([str(comp) for comp in key_components if comp])
    
    def _set_cache_with_ttl(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache with optional TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds. If None, uses the default TTL from settings.
        """
        if self.cache:
            self.cache.set(key, value, ttl)
            
    def _log_debug(self, message: str) -> None:
        """
        Log a debug message.
        
        Args:
            message: Message to log
        """
        logger.debug(message)
        
    def _log_info(self, message: str) -> None:
        """
        Log an info message.
        
        Args:
            message: Message to log
        """
        logger.info(message)
        
    def _log_warning(self, message: str) -> None:
        """
        Log a warning message.
        
        Args:
            message: Message to log
        """
        logger.warning(message)
        
    def _log_error(self, message: str) -> None:
        """
        Log an error message.
        
        Args:
            message: Message to log
        """
        logger.error(message)
        
    def _extract_resource_group_from_id(self, resource_id: str, default_rg: str = None) -> str:
        """
        Extract resource group name from an Azure resource ID.
        
        Args:
            resource_id: Azure resource ID
            default_rg: Default resource group to return if extraction fails
            
        Returns:
            Resource group name
        """
        parts = resource_id.split('/')
        if len(parts) >= 5 and parts[3].lower() == 'resourcegroups':
            return parts[4]
        return default_rg