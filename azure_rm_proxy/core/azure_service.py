"""Service layer for interacting with Azure resources."""

import logging

from .azure_clients import AzureClientFactory
from .caching import CacheStrategy
from .concurrency import ConcurrencyLimiter
from .mixins import (
    SubscriptionMixin,
    ResourceGroupMixin,
    VirtualMachineMixin,
    NetworkMixin,
    AADGroupMixin,
    RouteMixin,
)

logger = logging.getLogger(__name__)


class AzureResourceService(
    SubscriptionMixin,
    ResourceGroupMixin,
    VirtualMachineMixin,
    NetworkMixin,
    AADGroupMixin,
    RouteMixin,
):
    """
    Service layer for interacting with Azure resources.

    This class uses mixins to organize functionality by resource type:
    - SubscriptionMixin: Subscription-related operations
    - ResourceGroupMixin: Resource group-related operations
    - VirtualMachineMixin: VM-related operations
    - NetworkMixin: Network interface, NSG, and route-related operations
    - AADGroupMixin: Azure AD group-related operations
    - RouteMixin: Route table-related operations
    """

    def __init__(self, credential, cache: CacheStrategy, limiter: ConcurrencyLimiter):
        """
        Initialize the Azure Resource Service.

        Args:
            credential: Azure credential object
            cache: Cache strategy to use
            limiter: Concurrency limiter for API calls
        """
        self.credential = credential
        self.cache = cache
        self.limiter = limiter
        logger.info("AzureResourceService initialized with mixins")
