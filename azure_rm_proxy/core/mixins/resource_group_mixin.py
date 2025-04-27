"""Resource group functionality mixin for Azure Resource Service."""

import logging
from typing import List

from azure.core.exceptions import ResourceNotFoundError, ClientAuthenticationError

from ..azure_clients import AzureClientFactory
from ..models import ResourceGroupModel
from .base_mixin import BaseAzureResourceMixin

logger = logging.getLogger(__name__)


class ResourceGroupMixin(BaseAzureResourceMixin):
    """Mixin for resource group-related operations."""

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
        cache_key = self._get_cache_key(["resource_groups", subscription_id])
        self._log_debug(
            f"Attempting to get resource groups for subscription {subscription_id} with refresh_cache={refresh_cache}"
        )

        if not refresh_cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                self._log_debug(
                    f"Cache hit for resource groups in subscription {subscription_id}"
                )
                return self._validate_cached_data(cached_data, ResourceGroupModel)

        self._log_info(
            f"Fetching resource groups for subscription {subscription_id} from Azure"
        )
        try:
            resource_client = AzureClientFactory.create_resource_client(
                subscription_id, self.credential
            )

            async with self.limiter:
                self._log_debug(
                    f"Acquired concurrency limiter for resource groups in subscription {subscription_id}"
                )

                resource_groups = []
                for rg in resource_client.resource_groups.list():
                    rg_dict = {
                        "id": rg.id,
                        "name": rg.name,
                        "location": rg.location,
                        "tags": rg.tags,
                    }
                    resource_groups.append(ResourceGroupModel.model_validate(rg_dict))

                self._log_debug(
                    f"Released concurrency limiter for resource groups in subscription {subscription_id}"
                )

            self.cache.set(cache_key, resource_groups)
            self._log_info(
                f"Fetched {len(resource_groups)} resource groups for subscription {subscription_id}"
            )
            return resource_groups

        except ResourceNotFoundError as e:
            self._log_warning(f"Subscription {subscription_id} not found: {e}")
            raise
        except ClientAuthenticationError as e:
            self._log_error(f"Authentication error fetching resource groups: {e}")
            raise
        except Exception as e:
            self._log_error(
                f"Error fetching resource groups for subscription {subscription_id}: {e}"
            )
            raise
