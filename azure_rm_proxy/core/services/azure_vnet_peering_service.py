"""Azure Virtual Network Peering Service Implementation."""

import logging
import hashlib
from typing import List, Dict, Optional, Tuple, Set

from azure.mgmt.network import NetworkManagementClient
from azure.core.exceptions import ResourceNotFoundError

from ..models import VirtualNetworkPeeringPairModel
from ..caching import CacheStrategy
from .peering_service_interface import PeeringServiceInterface
from ..mixins.base_mixin import cached_azure_operation

logger = logging.getLogger(__name__)


class AzureVNetPeeringService(PeeringServiceInterface):
    """Service for Azure Virtual Network peering operations."""

    def __init__(
        self, credential, cache: Optional[CacheStrategy] = None, limiter=None, resource_service=None
    ):
        """
        Initialize the peering service with necessary dependencies.

        Args:
            credential: Azure credential for authentication
            cache: Cache strategy implementation
            limiter: Concurrency limiter
            resource_service: Reference to the parent resource service for client access
        """
        self.credential = credential
        self.cache = cache
        self.limiter = limiter
        self.resource_service = resource_service

    def generate_peering_pair_id(self, vnet1_id: str, vnet2_id: str) -> str:
        """
        Generate a consistent ID for a peering pair regardless of the order.

        Args:
            vnet1_id: First VNet ID
            vnet2_id: Second VNet ID

        Returns:
            A consistent ID for the peering pair
        """
        # Sort to ensure consistency
        vnet_ids = sorted([vnet1_id, vnet2_id])
        # Create a hash of the two IDs to use as a unique identifier
        combined = f"{vnet_ids[0]}:{vnet_ids[1]}"
        return hashlib.md5(combined.encode()).hexdigest()

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
        try:
            # Azure resource IDs follow this pattern:
            # /subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{vnet_name}
            parts = vnet_id.split("/")
            if len(parts) >= 9 and parts[1] == "subscriptions" and parts[3] == "resourceGroups":
                subscription_id = parts[2]
                resource_group = parts[4]
                vnet_name = parts[8]
                return (subscription_id, resource_group, vnet_name)
            else:
                logger.warning(f"Could not parse VNet ID: {vnet_id}")
                return None
        except Exception as e:
            logger.error(f"Error parsing VNet ID {vnet_id}: {str(e)}")
            return None

    async def _get_client(self, client_type: str, subscription_id: str):
        """
        Get an Azure client through the parent resource service.

        Args:
            client_type: Type of client to create ('network', etc.)
            subscription_id: Azure subscription ID

        Returns:
            Azure client instance
        """
        # Delegate client creation to the resource service
        if self.resource_service and hasattr(self.resource_service, "_get_client"):
            return await self.resource_service._get_client(client_type, subscription_id)
        else:
            raise RuntimeError("Resource service unavailable for client creation")

    def _extract_resource_group_from_id(self, resource_id: str, default_rg: str = None) -> str:
        """
        Extract resource group name from an Azure resource ID.

        Args:
            resource_id: Azure resource ID
            default_rg: Default resource group to return if extraction fails

        Returns:
            Resource group name
        """
        parts = resource_id.split("/")
        if len(parts) >= 5 and parts[3].lower() == "resourcegroups":
            return parts[4]
        return default_rg

    def _log_debug(self, message: str) -> None:
        logger.debug(message)

    def _log_info(self, message: str) -> None:
        logger.info(message)

    def _log_warning(self, message: str) -> None:
        logger.warning(message)

    def _log_error(self, message: str) -> None:
        logger.error(message)

    def _get_cache_key(self, key_components: list) -> str:
        """
        Create a standardized cache key from components.

        Args:
            key_components: List of strings to join for the cache key

        Returns:
            Standardized cache key
        """
        return ":".join([str(comp) for comp in key_components if comp])

    def _set_cache_with_ttl(self, key: str, value, ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache with optional TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        if not self.cache:
            return

        if ttl is not None and hasattr(self.cache, "set_with_ttl"):
            self.cache.set_with_ttl(key, value, ttl)
        else:
            self.cache.set(key, value)

    @cached_azure_operation(
        model_class=VirtualNetworkPeeringPairModel, cache_key_prefix="vnet_peering_report"
    )
    async def get_peering_report(
        self,
        subscription_id: str,
        resource_group_name: Optional[str] = None,
        refresh_cache: bool = False,
    ) -> List[VirtualNetworkPeeringPairModel]:
        """
        Generate a report of virtual network peerings.

        This method builds a comprehensive report of all peering relationships,
        showing both sides of each peering connection.

        Args:
            subscription_id: Azure subscription ID
            resource_group_name: Optional resource group name to filter by
            refresh_cache: Whether to refresh the cache

        Returns:
            List of VirtualNetworkPeeringPairModel objects representing peering pairs
        """
        self._log_debug(
            f"Generating peering report for subscription {subscription_id}"
            + (f", resource group {resource_group_name}" if resource_group_name else "")
        )

        try:
            # Get network client
            network_client = await self._get_client("network", subscription_id)

            # Get virtual networks
            all_vnets_raw = await self._fetch_virtual_networks(
                network_client, subscription_id, resource_group_name
            )

            self._log_debug(
                f"Found {len(all_vnets_raw)} virtual networks in subscription {subscription_id}"
            )

            # Process peerings
            peering_pairs = await self._process_vnets_for_peerings(
                all_vnets_raw, subscription_id, resource_group_name, refresh_cache
            )

            self._log_debug(f"Generated report with {len(peering_pairs)} peering relationships")
            return peering_pairs

        except Exception as e:
            self._log_error(f"Error generating peering report: {str(e)}")
            return []

    async def _fetch_virtual_networks(
        self,
        network_client: NetworkManagementClient,
        subscription_id: str,
        resource_group_name: Optional[str] = None,
    ) -> List:
        """
        Fetch virtual networks from Azure.

        Args:
            network_client: Azure network client
            subscription_id: Subscription ID
            resource_group_name: Optional resource group name

        Returns:
            List of virtual network objects
        """
        try:
            # Get virtual networks from API
            if resource_group_name:
                vnets_iterator = network_client.virtual_networks.list(resource_group_name)
            else:
                vnets_iterator = network_client.virtual_networks.list_all()

            # Materialize the iterator to avoid connection issues on multiple iterations
            return list(vnets_iterator)
        except Exception as e:
            self._log_error(f"Error fetching virtual networks: {str(e)}")
            return []

    async def _process_vnets_for_peerings(
        self,
        vnets: List,
        subscription_id: str,
        resource_group_name: Optional[str] = None,
        refresh_cache: bool = False,
    ) -> List[VirtualNetworkPeeringPairModel]:
        """
        Process virtual networks to find and analyze peerings.

        Args:
            vnets: List of virtual networks
            subscription_id: Subscription ID
            resource_group_name: Optional resource group name
            refresh_cache: Whether to refresh the cache

        Returns:
            List of peering pair models
        """
        # Initialize structures to track peerings
        peering_pairs = []
        processed_pairs: Set[str] = set()

        # For each VNet, get peering information
        for vnet_raw in vnets:
            try:
                # Skip invalid VNets
                if (
                    not hasattr(vnet_raw, "id")
                    or not hasattr(vnet_raw, "name")
                    or not vnet_raw.id
                    or not vnet_raw.name
                ):
                    continue

                vnet_id = vnet_raw.id
                vnet_name = vnet_raw.name

                # Extract resource group from ID
                vnet_resource_group = self._extract_resource_group_from_id(
                    vnet_id, resource_group_name
                )

                self._log_debug(
                    f"Processing VNet: {vnet_name} in resource group {vnet_resource_group}"
                )

                # Check if VNet has peerings
                if (
                    not hasattr(vnet_raw, "virtual_network_peerings")
                    or not vnet_raw.virtual_network_peerings
                ):
                    continue

                # Process each peering in the VNet
                peerings = vnet_raw.virtual_network_peerings
                self._log_debug(f"Found {len(peerings)} peerings for VNet {vnet_name}")

                for peering in peerings:
                    await self._process_single_peering(
                        peering,
                        vnet_id,
                        vnet_name,
                        vnet_resource_group,
                        subscription_id,
                        processed_pairs,
                        peering_pairs,
                        refresh_cache,
                    )
            except Exception as e:
                self._log_error(
                    f"Error processing VNet {getattr(vnet_raw, 'name', 'unknown')}: {str(e)}"
                )

        return peering_pairs

    async def _process_single_peering(
        self,
        peering,
        vnet_id: str,
        vnet_name: str,
        vnet_resource_group: str,
        subscription_id: str,
        processed_pairs: Set[str],
        peering_pairs: List[VirtualNetworkPeeringPairModel],
        refresh_cache: bool = False,
    ) -> None:
        """
        Process a single peering relationship.

        Args:
            peering: The peering object
            vnet_id: ID of the VNet containing the peering
            vnet_name: Name of the VNet containing the peering
            vnet_resource_group: Resource group of the VNet
            subscription_id: Subscription ID
            processed_pairs: Set of processed peering pair IDs
            peering_pairs: List to add peering pair models to
            refresh_cache: Whether to refresh the cache
        """
        try:
            # Skip invalid peerings
            if not hasattr(peering, "name") or not peering.name:
                return

            # Get remote VNet ID
            remote_vnet_id = self._get_remote_vnet_id(peering)
            if not remote_vnet_id:
                self._log_warning(f"Peering {peering.name} has no remote VNet ID")
                return

            # Generate unique ID for this peering pair
            pair_id = self.generate_peering_pair_id(vnet_id, remote_vnet_id)

            # Skip if already processed
            if pair_id in processed_pairs:
                return

            processed_pairs.add(pair_id)
            self._log_debug(
                f"Processing peering pair: {pair_id} between {vnet_name} and remote VNet"
            )

            # Extract local VNet data
            vnet_data = {
                "id": vnet_id,
                "name": vnet_name,
                "resource_group": vnet_resource_group,
                "subscription_id": subscription_id,
            }

            # Extract peering data
            peering_data = self._extract_peering_data(peering)

            # Try to get info on remote VNet
            remote_vnet_info = await self.get_vnet_info_from_id(remote_vnet_id, refresh_cache)

            if not remote_vnet_info:
                # Create partial report if remote VNet can't be accessed
                peering_pair = self._create_partial_peering_pair(
                    vnet_data, peering_data, remote_vnet_id
                )
                peering_pairs.append(peering_pair)
                return

            # Process complete peering relationship
            await self._process_complete_peering(
                vnet_data, peering_data, remote_vnet_id, remote_vnet_info, peering_pairs
            )

        except Exception as e:
            self._log_error(
                f"Error processing peering {getattr(peering, 'name', 'unknown')}: {str(e)}"
            )

    def _get_remote_vnet_id(self, peering) -> Optional[str]:
        """
        Extract remote VNet ID from a peering object.

        Args:
            peering: The peering object

        Returns:
            Remote VNet ID or None if not available
        """
        if (
            hasattr(peering, "remote_virtual_network")
            and peering.remote_virtual_network
            and hasattr(peering.remote_virtual_network, "id")
        ):
            return peering.remote_virtual_network.id
        return None

    def _extract_peering_data(self, peering) -> Dict:
        """
        Extract data from a peering object into a standardized dictionary.

        Args:
            peering: The peering object

        Returns:
            Dictionary with peering data
        """
        return {
            "id": peering.id if hasattr(peering, "id") else "",
            "name": peering.name,
            "remote_virtual_network_id": self._get_remote_vnet_id(peering) or "",
            "allow_virtual_network_access": (
                peering.allow_virtual_network_access
                if hasattr(peering, "allow_virtual_network_access")
                else True
            ),
            "allow_forwarded_traffic": (
                peering.allow_forwarded_traffic
                if hasattr(peering, "allow_forwarded_traffic")
                else False
            ),
            "allow_gateway_transit": (
                peering.allow_gateway_transit
                if hasattr(peering, "allow_gateway_transit")
                else False
            ),
            "use_remote_gateways": (
                peering.use_remote_gateways if hasattr(peering, "use_remote_gateways") else False
            ),
            "peering_state": (
                peering.peering_state if hasattr(peering, "peering_state") else "Unknown"
            ),
            "provisioning_state": (
                peering.provisioning_state if hasattr(peering, "provisioning_state") else "Unknown"
            ),
        }

    async def _process_complete_peering(
        self,
        vnet_data: Dict,
        peering_data: Dict,
        remote_vnet_id: str,
        remote_vnet_info: Tuple[str, str, str],
        peering_pairs: List[VirtualNetworkPeeringPairModel],
    ) -> None:
        """
        Process a complete peering relationship where both sides are accessible.

        Args:
            vnet_data: Dictionary with local VNet data
            peering_data: Dictionary with peering data
            remote_vnet_id: The ID of the remote VNet
            remote_vnet_info: Tuple of (subscription_id, resource_group, vnet_name)
            peering_pairs: List to add peering pair models to
        """
        try:
            remote_subscription_id, remote_resource_group, remote_vnet_name = remote_vnet_info

            # Get the remote VNet
            remote_network_client = await self._get_client("network", remote_subscription_id)
            remote_vnet_raw = remote_network_client.virtual_networks.get(
                remote_resource_group, remote_vnet_name
            )

            # Extract remote VNet data
            remote_vnet_data = {
                "id": remote_vnet_raw.id,
                "name": remote_vnet_name,
                "resource_group": remote_resource_group,
                "subscription_id": remote_subscription_id,
            }

            # Find return peering (from remote to local)
            return_peering_data = self._find_return_peering(remote_vnet_raw, vnet_id)

            # Create complete peering pair
            peering_pair = self._create_complete_peering_pair(
                vnet_data, peering_data, remote_vnet_data, return_peering_data
            )
            peering_pairs.append(peering_pair)

        except Exception as e:
            # If remote VNet access fails, create a partial pair
            self._log_error(f"Error accessing remote VNet {remote_vnet_info[2]}: {str(e)}")
            peering_pair = self._create_partial_peering_pair(
                vnet_data, peering_data, remote_vnet_id
            )
            peering_pairs.append(peering_pair)

    def _find_return_peering(self, remote_vnet, local_vnet_id: str) -> Optional[Dict]:
        """
        Find the return peering from remote VNet to local VNet.

        Args:
            remote_vnet: The remote VNet object
            local_vnet_id: ID of the local VNet

        Returns:
            Dictionary with return peering data, or None if not found
        """
        if (
            not hasattr(remote_vnet, "virtual_network_peerings")
            or not remote_vnet.virtual_network_peerings
        ):
            return None

        for peering in remote_vnet.virtual_network_peerings:
            remote_peering_target_id = self._get_remote_vnet_id(peering)

            if remote_peering_target_id == local_vnet_id:
                # Found the return peering
                return {
                    "id": peering.id if hasattr(peering, "id") else "",
                    "name": peering.name if hasattr(peering, "name") else "",
                    "remote_virtual_network_id": local_vnet_id,
                    "peering_state": (
                        peering.peering_state if hasattr(peering, "peering_state") else "Unknown"
                    ),
                }

        return None

    def _create_partial_peering_pair(
        self, vnet_data: Dict, peering_data: Dict, remote_vnet_id: str
    ) -> VirtualNetworkPeeringPairModel:
        """
        Create a partial peering pair model when only one side is accessible.

        Args:
            vnet_data: Dictionary with local VNet data
            peering_data: Dictionary with peering data
            remote_vnet_id: The ID of the remote VNet

        Returns:
            A VirtualNetworkPeeringPairModel with partial information
        """
        # Try to extract information from the remote VNet ID
        remote_parts = remote_vnet_id.split("/")
        remote_subscription_id = ""
        remote_resource_group = ""
        remote_vnet_name = ""

        if len(remote_parts) >= 9:
            remote_subscription_id = remote_parts[2]
            remote_resource_group = remote_parts[4]
            remote_vnet_name = remote_parts[8]

        # Create a peering pair with available information
        return VirtualNetworkPeeringPairModel(
            peering_id=self.generate_peering_pair_id(vnet_data["id"], remote_vnet_id),
            vnet1_id=vnet_data["id"],
            vnet1_name=vnet_data["name"],
            vnet1_resource_group=vnet_data["resource_group"],
            vnet1_subscription_id=vnet_data["subscription_id"],
            vnet1_to_vnet2_state=peering_data["peering_state"],
            vnet2_id=remote_vnet_id,
            vnet2_name=remote_vnet_name,
            vnet2_resource_group=remote_resource_group,
            vnet2_subscription_id=remote_subscription_id,
            vnet2_to_vnet1_state="Unknown",  # We don't have the return peering information
            allow_virtual_network_access=peering_data["allow_virtual_network_access"],
            allow_forwarded_traffic=peering_data["allow_forwarded_traffic"],
            allow_gateway_transit=peering_data["allow_gateway_transit"],
            use_remote_gateways=peering_data["use_remote_gateways"],
            provisioning_state=peering_data["provisioning_state"],
            connected=False,  # We can't confirm the connection is established in both directions
        )

    def _create_complete_peering_pair(
        self,
        vnet1_data: Dict,
        peering1to2_data: Dict,
        vnet2_data: Dict,
        peering2to1_data: Optional[Dict],
    ) -> VirtualNetworkPeeringPairModel:
        """
        Create a complete peering pair model using data from both sides.

        Args:
            vnet1_data: Dictionary with first VNet data
            peering1to2_data: Dictionary with peering data from first to second VNet
            vnet2_data: Dictionary with second VNet data
            peering2to1_data: Dictionary with peering data from second to first VNet (may be None)

        Returns:
            A complete VirtualNetworkPeeringPairModel
        """
        # Check if the peering is connected in both directions
        connected = False
        if peering2to1_data:
            connected = (
                peering1to2_data["peering_state"] == "Connected"
                and peering2to1_data["peering_state"] == "Connected"
            )

        # Create the peering pair model
        return VirtualNetworkPeeringPairModel(
            peering_id=self.generate_peering_pair_id(vnet1_data["id"], vnet2_data["id"]),
            vnet1_id=vnet1_data["id"],
            vnet1_name=vnet1_data["name"],
            vnet1_resource_group=vnet1_data["resource_group"],
            vnet1_subscription_id=vnet1_data["subscription_id"],
            vnet1_to_vnet2_state=peering1to2_data["peering_state"],
            vnet2_id=vnet2_data["id"],
            vnet2_name=vnet2_data["name"],
            vnet2_resource_group=vnet2_data["resource_group"],
            vnet2_subscription_id=vnet2_data["subscription_id"],
            vnet2_to_vnet1_state=(
                peering2to1_data["peering_state"] if peering2to1_data else "NotConfigured"
            ),
            allow_virtual_network_access=peering1to2_data["allow_virtual_network_access"],
            allow_forwarded_traffic=peering1to2_data["allow_forwarded_traffic"],
            allow_gateway_transit=peering1to2_data["allow_gateway_transit"],
            use_remote_gateways=peering1to2_data["use_remote_gateways"],
            provisioning_state=peering1to2_data["provisioning_state"],
            connected=connected,
        )
