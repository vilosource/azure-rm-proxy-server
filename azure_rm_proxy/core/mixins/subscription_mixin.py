"""Subscription functionality mixin for Azure Resource Service."""

import logging
from typing import List

from azure.core.exceptions import ClientAuthenticationError

from ..azure_clients import AzureClientFactory
from ..models import SubscriptionModel
from .base_mixin import BaseAzureResourceMixin

logger = logging.getLogger(__name__)

class SubscriptionMixin(BaseAzureResourceMixin):
    """Mixin for subscription-related operations."""
    
    async def get_subscriptions(self, refresh_cache: bool = False) -> List[SubscriptionModel]:
        """
        Get all subscriptions.
        
        Args:
            refresh_cache: Whether to refresh the cache
            
        Returns:
            List of subscription models
        """
        cache_key = self._get_cache_key(["subscriptions"])
        self._log_debug(f"Attempting to get subscriptions with refresh_cache={refresh_cache}")
        
        if not refresh_cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                self._log_debug("Cache hit for subscriptions")
                return cached_data

        self._log_info("Fetching subscriptions from Azure")
        try:
            async with self.limiter:
                self._log_debug("Acquired concurrency limiter for subscriptions")
                
                subscription_client = AzureClientFactory.create_subscription_client(self.credential)
                subscriptions = []
                
                for sub in subscription_client.subscriptions.list():
                    sub_dict = {
                        "id": sub.subscription_id,
                        "name": sub.display_name,
                        "display_name": sub.display_name,
                        "state": sub.state
                    }
                    subscriptions.append(SubscriptionModel.model_validate(sub_dict))
                
                self._log_debug("Released concurrency limiter for subscriptions")
                
            self.cache.set(cache_key, subscriptions)
            self._log_info(f"Fetched {len(subscriptions)} subscriptions")
            return subscriptions
            
        except ClientAuthenticationError as e:
            self._log_error(f"Authentication error fetching subscriptions: {e}")
            raise
        except Exception as e:
            self._log_error(f"Error fetching subscriptions: {e}")
            raise