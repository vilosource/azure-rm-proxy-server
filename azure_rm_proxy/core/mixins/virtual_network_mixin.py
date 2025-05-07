"""Virtual Network functionality mixin for Azure Resource Service."""

import logging
import traceback
import hashlib
from typing import List, Dict, Optional, Union, Set, Tuple

from azure.core.exceptions import ResourceNotFoundError
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.network.models import (
    VirtualNetwork,
    Subnet,
    VirtualNetworkPeering,
)

from ..models import (
    VirtualNetworkModel,
    SubnetModel,
    VirtualNetworkPeeringModel,
    VirtualNetworkPeeringPairModel,
)
from .base_mixin import BaseAzureResourceMixin, cached_azure_operation

logger = logging.getLogger(__name__)


class VirtualNetworkMixin(BaseAzureResourceMixin):
    """Mixin for virtual network-related operations."""

    @cached_azure_operation(model_class=VirtualNetworkModel, cache_key_prefix="virtual_networks")
    async def list_virtual_networks(
        self,
        subscription_id: str,
        resource_group_name: Optional[str] = None,
        refresh_cache: bool = False,
    ) -> List[VirtualNetworkModel]:
        """
        List virtual networks in a subscription or resource group.

        Args:
            subscription_id: Azure subscription ID
            resource_group_name: Optional resource group name to filter by
            refresh_cache: Whether to refresh the cache

        Returns:
            List of VirtualNetworkModel objects
        """
        self._log_debug(
            f"Listing virtual networks in subscription {subscription_id}"
            + (f", resource group {resource_group_name}" if resource_group_name else "")
        )

        try:
            # Get network client with concurrency control
            network_client = await self._get_client("network", subscription_id)

            # Get virtual networks
            if resource_group_name:
                vnets = list(network_client.virtual_networks.list(resource_group_name))
            else:
                vnets = list(network_client.virtual_networks.list_all())

            # Convert to models
            result = []
            for vnet in vnets:
                if vnet.id and vnet.name:
                    # Get resource group name from ID
                    resource_group = self._extract_resource_group_from_id(
                        vnet.id, resource_group_name
                    )

                    # Extract address space prefixes
                    address_space = []
                    if hasattr(vnet, "address_space") and vnet.address_space:
                        if hasattr(vnet.address_space, "address_prefixes"):
                            address_space = vnet.address_space.address_prefixes or []

                    # Extract DNS servers
                    dns_servers = []
                    if hasattr(vnet, "dhcp_options") and vnet.dhcp_options:
                        if hasattr(vnet.dhcp_options, "dns_servers"):
                            dns_servers = vnet.dhcp_options.dns_servers or []

                    # Basic model with minimal information
                    vnet_model = self._convert_to_model(
                        vnet,
                        VirtualNetworkModel,
                        resource_group=resource_group,
                        address_space=address_space,
                        dns_servers=dns_servers,
                        subscription_id=subscription_id,
                        # Empty lists for subnets/peerings - will be populated if get_virtual_network is called
                        subnets=[],
                        peerings=[],
                    )
                    result.append(vnet_model)

            self._log_debug(f"Found {len(result)} virtual networks")
            return result
        except Exception as e:
            self._log_error(f"Error listing virtual networks: {str(e)}")
            return []

    @cached_azure_operation(
        model_class=VirtualNetworkModel, cache_key_prefix="virtual_network_detail"
    )
    async def get_virtual_network(
        self,
        subscription_id: str,
        resource_group_name: str,
        vnet_name: str,
        refresh_cache: bool = False,
    ) -> Optional[VirtualNetworkModel]:
        """
        Get details of a specific virtual network.

        Args:
            subscription_id: Azure subscription ID
            resource_group_name: Resource group name
            vnet_name: Virtual network name
            refresh_cache: Whether to refresh the cache

        Returns:
            VirtualNetworkModel object if found, None otherwise
        """
        self._log_debug(
            f"Getting virtual network {vnet_name} in resource group {resource_group_name}"
        )

        try:
            # Get network client with concurrency control
            network_client = await self._get_client("network", subscription_id)

            # Get the virtual network with the given name
            vnet = network_client.virtual_networks.get(resource_group_name, vnet_name)

            # Extract address space prefixes
            address_space = []
            if hasattr(vnet, "address_space") and vnet.address_space:
                if hasattr(vnet.address_space, "address_prefixes"):
                    address_space = vnet.address_space.address_prefixes or []

            # Extract DNS servers
            dns_servers = []
            if hasattr(vnet, "dhcp_options") and vnet.dhcp_options:
                if hasattr(vnet.dhcp_options, "dns_servers"):
                    dns_servers = vnet.dhcp_options.dns_servers or []

            # Get subnets
            subnets = await self._fetch_subnets(vnet)

            # Get peerings
            peerings = await self._fetch_peerings(vnet, network_client, resource_group_name)

            # Create the virtual network model
            vnet_model = self._convert_to_model(
                vnet,
                VirtualNetworkModel,
                resource_group=resource_group_name,
                address_space=address_space,
                dns_servers=dns_servers,
                subnets=subnets,
                peerings=peerings,
                subscription_id=subscription_id,
            )

            return vnet_model
        except ResourceNotFoundError:
            self._log_warning(f"Virtual network {vnet_name} not found")
            return None
        except Exception as e:
            self._log_error(f"Error getting virtual network {vnet_name}: {str(e)}")
            return None

    async def _fetch_subnets(self, vnet: VirtualNetwork) -> List[SubnetModel]:
        """
        Extract subnet information from a virtual network.

        Args:
            vnet: Azure virtual network object

        Returns:
            List of SubnetModel objects
        """
        subnets = []

        if not (hasattr(vnet, "subnets") and vnet.subnets):
            return subnets

        for subnet in vnet.subnets:
            # Extract NSG ID if present
            nsg_id = None
            if (
                hasattr(subnet, "network_security_group")
                and subnet.network_security_group
                and hasattr(subnet.network_security_group, "id")
            ):
                nsg_id = subnet.network_security_group.id

            # Extract route table ID if present
            route_table_id = None
            if (
                hasattr(subnet, "route_table")
                and subnet.route_table
                and hasattr(subnet.route_table, "id")
            ):
                route_table_id = subnet.route_table.id

            # Extract service endpoints
            service_endpoints = []
            if hasattr(subnet, "service_endpoints") and subnet.service_endpoints:
                for endpoint in subnet.service_endpoints:
                    if hasattr(endpoint, "service") and endpoint.service:
                        endpoint_model = {
                            "service": endpoint.service,
                            "locations": [],
                            "provisioning_state": (
                                endpoint.provisioning_state
                                if hasattr(endpoint, "provisioning_state")
                                else None
                            ),
                        }

                        # Handle locations properly as a list
                        if hasattr(endpoint, "locations") and endpoint.locations:
                            # Ensure locations is treated as a list even if it's a single item
                            endpoint_model["locations"] = list(endpoint.locations)

                        from ..models import ServiceEndpointModel

                        service_endpoints.append(
                            ServiceEndpointModel.model_validate(endpoint_model)
                        )

            # Create subnet model
            subnet_model = self._convert_to_model(
                subnet,
                SubnetModel,
                network_security_group_id=nsg_id,
                route_table_id=route_table_id,
                service_endpoints=service_endpoints,
            )
            subnets.append(subnet_model)

        return subnets

    async def _fetch_peerings(
        self,
        vnet: VirtualNetwork,
        network_client: NetworkManagementClient,
        resource_group_name: str,
    ) -> List[VirtualNetworkPeeringModel]:
        """
        Extract peering information from a virtual network.

        Args:
            vnet: Azure virtual network object
            network_client: Azure network client
            resource_group_name: Resource group name

        Returns:
            List of VirtualNetworkPeeringModel objects
        """
        peerings = []

        # Check if the virtual network has any peerings
        if not (hasattr(vnet, "virtual_network_peerings") and vnet.virtual_network_peerings):
            return peerings

        for peering in vnet.virtual_network_peerings:
            remote_vnet_id = ""
            if (
                hasattr(peering, "remote_virtual_network")
                and peering.remote_virtual_network
                and hasattr(peering.remote_virtual_network, "id")
            ):
                remote_vnet_id = peering.remote_virtual_network.id

            peering_model = self._convert_to_model(
                peering, VirtualNetworkPeeringModel, remote_virtual_network_id=remote_vnet_id
            )
            peerings.append(peering_model)

        return peerings

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
            # Get all virtual networks with basic info
            network_client = await self._get_client("network", subscription_id)

            # Get virtual networks directly from the API instead of using list_virtual_networks
            # This avoids potential model validation issues in the list_virtual_networks method
            if resource_group_name:
                vnets_iterator = network_client.virtual_networks.list(resource_group_name)
            else:
                vnets_iterator = network_client.virtual_networks.list_all()

            # Materialize the iterator to a list to avoid issues with multiple iterations
            all_vnets_raw = list(vnets_iterator)
            self._log_debug(
                f"Found {len(all_vnets_raw)} virtual networks in subscription {subscription_id}"
            )

            # Initialize structures to track peerings
            peering_pairs = []
            processed_pairs = set()  # To avoid duplicates

            # For each VNet, get peering information directly
            for vnet_raw in all_vnets_raw:
                try:
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

                    # Get peerings directly rather than through the detailed VNet model
                    # This avoids issues with subnet validation errors
                    if (
                        hasattr(vnet_raw, "virtual_network_peerings")
                        and vnet_raw.virtual_network_peerings
                    ):
                        peerings = vnet_raw.virtual_network_peerings
                        self._log_debug(f"Found {len(peerings)} peerings for VNet {vnet_name}")

                        for peering in peerings:
                            try:
                                # Skip if peering is missing essential data
                                if not hasattr(peering, "name") or not peering.name:
                                    continue

                                # Get remote VNet ID
                                remote_vnet_id = None
                                if (
                                    hasattr(peering, "remote_virtual_network")
                                    and peering.remote_virtual_network
                                    and hasattr(peering.remote_virtual_network, "id")
                                ):
                                    remote_vnet_id = peering.remote_virtual_network.id

                                if not remote_vnet_id:
                                    self._log_warning(
                                        f"Peering {peering.name} has no remote VNet ID"
                                    )
                                    continue

                                # Create a unique identifier for this peering pair
                                pair_id = self._generate_peering_pair_id(vnet_id, remote_vnet_id)

                                # Skip if already processed
                                if pair_id in processed_pairs:
                                    continue

                                processed_pairs.add(pair_id)
                                self._log_debug(
                                    f"Processing peering pair: {pair_id} between {vnet_name} and remote VNet"
                                )

                                # Extract vnet data (avoid using models that might fail validation)
                                vnet_data = {
                                    "id": vnet_id,
                                    "name": vnet_name,
                                    "resource_group": vnet_resource_group,
                                    "subscription_id": subscription_id,
                                }

                                # Extract peering data
                                peering_data = {
                                    "id": peering.id if hasattr(peering, "id") else "",
                                    "name": peering.name,
                                    "remote_virtual_network_id": remote_vnet_id,
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
                                        peering.use_remote_gateways
                                        if hasattr(peering, "use_remote_gateways")
                                        else False
                                    ),
                                    "peering_state": (
                                        peering.peering_state
                                        if hasattr(peering, "peering_state")
                                        else "Unknown"
                                    ),
                                    "provisioning_state": (
                                        peering.provisioning_state
                                        if hasattr(peering, "provisioning_state")
                                        else "Unknown"
                                    ),
                                }

                                # Try to get info on remote VNet
                                remote_vnet_info = await self._get_vnet_info_from_id(
                                    remote_vnet_id, refresh_cache
                                )

                                if not remote_vnet_info:
                                    # Create a partial report if remote VNet can't be accessed
                                    peering_pair = self._create_partial_peering_pair_directly(
                                        vnet_data, peering_data, remote_vnet_id
                                    )
                                    peering_pairs.append(peering_pair)
                                    continue

                                # Try to find the return peering (from remote to local)
                                remote_subscription_id, remote_resource_group, remote_vnet_name = (
                                    remote_vnet_info
                                )

                                try:
                                    # Get the remote VNet directly from the API
                                    remote_network_client = await self._get_client(
                                        "network", remote_subscription_id
                                    )
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

                                    # Find return peering
                                    return_peering_data = None
                                    if (
                                        hasattr(remote_vnet_raw, "virtual_network_peerings")
                                        and remote_vnet_raw.virtual_network_peerings
                                    ):
                                        for (
                                            remote_peering
                                        ) in remote_vnet_raw.virtual_network_peerings:
                                            remote_peering_target_id = None
                                            if (
                                                hasattr(remote_peering, "remote_virtual_network")
                                                and remote_peering.remote_virtual_network
                                                and hasattr(
                                                    remote_peering.remote_virtual_network, "id"
                                                )
                                            ):
                                                remote_peering_target_id = (
                                                    remote_peering.remote_virtual_network.id
                                                )

                                            if remote_peering_target_id == vnet_id:
                                                # Found the return peering
                                                return_peering_data = {
                                                    "id": (
                                                        remote_peering.id
                                                        if hasattr(remote_peering, "id")
                                                        else ""
                                                    ),
                                                    "name": (
                                                        remote_peering.name
                                                        if hasattr(remote_peering, "name")
                                                        else ""
                                                    ),
                                                    "remote_virtual_network_id": vnet_id,
                                                    "peering_state": (
                                                        remote_peering.peering_state
                                                        if hasattr(remote_peering, "peering_state")
                                                        else "Unknown"
                                                    ),
                                                }
                                                break

                                    # Create complete peering pair info
                                    peering_pair = self._create_peering_pair_directly(
                                        vnet_data,
                                        peering_data,
                                        remote_vnet_data,
                                        return_peering_data,
                                    )
                                    peering_pairs.append(peering_pair)
                                except Exception as e:
                                    # If remote VNet access fails, create a partial pair
                                    self._log_error(
                                        f"Error accessing remote VNet {remote_vnet_name}: {str(e)}"
                                    )
                                    peering_pair = self._create_partial_peering_pair_directly(
                                        vnet_data, peering_data, remote_vnet_id
                                    )
                                    peering_pairs.append(peering_pair)
                            except Exception as e:
                                self._log_error(
                                    f"Error processing peering {getattr(peering, 'name', 'unknown')}: {str(e)}"
                                )
                except Exception as e:
                    self._log_error(
                        f"Error processing VNet {getattr(vnet_raw, 'name', 'unknown')}: {str(e)}"
                    )

            self._log_debug(f"Generated report with {len(peering_pairs)} peering relationships")
            return peering_pairs

        except Exception as e:
            self._log_error(f"Error generating peering report: {str(e)}")
            # Return empty list in case of errors
            return []

    def _create_partial_peering_pair_directly(
        self, vnet_data: Dict, peering_data: Dict, remote_vnet_id: str
    ) -> VirtualNetworkPeeringPairModel:
        """
        Create a partial peering pair model using raw data dictionaries.

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
            peering_id=self._generate_peering_pair_id(vnet_data["id"], remote_vnet_id),
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

    def _create_peering_pair_directly(
        self,
        vnet1_data: Dict,
        peering1to2_data: Dict,
        vnet2_data: Dict,
        peering2to1_data: Optional[Dict],
    ) -> VirtualNetworkPeeringPairModel:
        """
        Create a complete peering pair model using raw data dictionaries.

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
            peering_id=self._generate_peering_pair_id(vnet1_data["id"], vnet2_data["id"]),
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
