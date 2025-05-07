"""Interface for virtual network peering services."""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple

from ..models import VirtualNetworkPeeringPairModel


class PeeringServiceInterface(ABC):
    """Interface defining the contract for peering services."""

    @abstractmethod
    async def get_peering_report(
        self,
        subscription_id: str,
        resource_group_name: Optional[str] = None,
        refresh_cache: bool = False,
    ) -> List[VirtualNetworkPeeringPairModel]:
        """
        Generate a report of virtual network peerings.

        Args:
            subscription_id: Azure subscription ID
            resource_group_name: Optional resource group name to filter by
            refresh_cache: Whether to refresh the cache

        Returns:
            List of VirtualNetworkPeeringPairModel objects
        """
        pass

    @abstractmethod
    def generate_peering_pair_id(self, vnet1_id: str, vnet2_id: str) -> str:
        """
        Generate a consistent identifier for a peering pair regardless of the order.

        Args:
            vnet1_id: First VNet ID
            vnet2_id: Second VNet ID

        Returns:
            A consistent ID for the peering pair
        """
        pass

    @abstractmethod
    async def get_vnet_info_from_id(
        self, vnet_id: str, refresh_cache: bool = False
    ) -> Optional[Tuple[str, str, str]]:
        """
        Extract subscription ID, resource group, and VNet name from a VNet ID.

        Args:
            vnet_id: The full Azure resource ID of the virtual network
            refresh_cache: Whether to refresh the cache

        Returns:
            Tuple of (subscription_id, resource_group, vnet_name) or None if parsing fails
        """
        pass
