"""Subscription functionality mixin for Azure Resource Service."""

import logging
from typing import List

from azure.core.exceptions import ClientAuthenticationError

from ..azure_clients import AzureClientFactory
from ..models import SubscriptionModel
from .base_mixin import BaseAzureResourceMixin, cached_azure_operation

logger = logging.getLogger(__name__)


class SubscriptionMixin(BaseAzureResourceMixin):
    """Mixin for subscription-related operations."""

    @cached_azure_operation(
        model_class=SubscriptionModel, cache_key_prefix="subscriptions"
    )
    async def get_subscriptions(
        self, refresh_cache: bool = False
    ) -> List[SubscriptionModel]:
        """
        Get all subscriptions.

        Args:
            refresh_cache: Whether to refresh the cache

        Returns:
            List of subscription models
        """
        # Get subscription client with concurrency control
        subscription_client = await self._get_client("subscription", None)

        subscriptions = []
        for sub in subscription_client.subscriptions.list():
            # Use the helper method to convert Azure object to Pydantic model
            subscription = self._convert_to_model(
                sub, SubscriptionModel, id=sub.subscription_id, name=sub.display_name
            )
            subscriptions.append(subscription)

        self._log_info(f"Fetched {len(subscriptions)} subscriptions")
        return subscriptions
