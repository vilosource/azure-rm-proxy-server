"""Mixin modules for Azure Resource Service."""

from .base_mixin import BaseAzureResourceMixin
from .subscription_mixin import SubscriptionMixin
from .resource_group_mixin import ResourceGroupMixin
from .virtual_machine_mixin import VirtualMachineMixin
from .network_mixin import NetworkMixin
from .aad_group_mixin import AADGroupMixin
from .route_mixin import RouteMixin

__all__ = [
    "BaseAzureResourceMixin",
    "SubscriptionMixin",
    "ResourceGroupMixin",
    "VirtualMachineMixin",
    "NetworkMixin",
    "AADGroupMixin",
    "RouteMixin",
]
