"""Resource group functionality mixin for Azure Resource Service."""

import logging
from typing import List

from azure.core.exceptions import ResourceNotFoundError, ClientAuthenticationError

from ..azure_clients import AzureClientFactory
from ..models import ResourceGroupModel
from .base_mixin import BaseAzureResourceMixin, cached_azure_operation

logger = logging.getLogger(__name__)


class ResourceGroupMixin(BaseAzureResourceMixin):
    """Mixin for resource group-related operations."""

    @cached_azure_operation(model_class=ResourceGroupModel)
    async def get_resource_groups(
        self, subscription_id: str, refresh_cache: bool = False
    ) -> List[ResourceGroupModel]:
        """
        Get all resource groups for a subscription.

        Args:
            subscription_id: Azure subscription ID
            refresh_cache: Whether to refresh the cache

        Returns:
            List of resource group models
        """
        # Get resource client with concurrency control
        resource_client = await self._get_client("resource", subscription_id)

        resource_groups = []
        for rg in resource_client.resource_groups.list():
            # Use the helper method to convert Azure object to Pydantic model
            resource_group = self._convert_to_model(rg, ResourceGroupModel)
            resource_groups.append(resource_group)

        self._log_info(
            f"Fetched {len(resource_groups)} resource groups for subscription {subscription_id}"
        )
        return resource_groups
