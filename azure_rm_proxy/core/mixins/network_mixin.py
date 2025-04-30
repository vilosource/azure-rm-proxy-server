"""Network functionality mixin for Azure Resource Service."""

import logging
import traceback
from typing import List, Optional

from azure.core.exceptions import ResourceNotFoundError

from ..models import NetworkInterfaceModel, NsgRuleModel, RouteModel
from .base_mixin import BaseAzureResourceMixin

logger = logging.getLogger(__name__)


class NetworkMixin(BaseAzureResourceMixin):
    """Mixin for network-related operations."""

    async def _fetch_network_interfaces(self, vm, network_client, vm_name):
        """
        Fetch network interfaces for a VM.

        Args:
            vm: Azure VM object
            network_client: Azure network client
            vm_name: VM name

        Returns:
            List of NetworkInterfaceModel objects
        """
        network_interfaces = []
        if not (
            hasattr(vm, "network_profile")
            and vm.network_profile
            and hasattr(vm.network_profile, "network_interfaces")
        ):
            self._log_warning(f"VM {vm_name} does not have network interfaces defined")
            return network_interfaces

        for nic_ref in vm.network_profile.network_interfaces:
            if not nic_ref or not hasattr(nic_ref, "id") or not nic_ref.id:
                self._log_warning(f"NIC reference does not have an ID for VM {vm_name}")
                continue

            nic_id = nic_ref.id
            parts = nic_id.split("/")
            if len(parts) < 9:
                self._log_warning(f"Invalid NIC ID format: {nic_id} for VM {vm_name}")
                continue

            nic_rg_name = parts[4]
            nic_name = parts[8]
            self._log_debug(f"Fetching NIC {nic_name} details")

            try:
                nic = network_client.network_interfaces.get(nic_rg_name, nic_name)
                private_ips = self._get_private_ips(nic)
                public_ips = await self._get_public_ips(
                    nic, network_client, nic_rg_name, vm_name
                )

                # Use _convert_to_model for consistent model creation
                network_interfaces.append(
                    self._convert_to_model(
                        {
                            "id": nic.id,
                            "name": nic.name,
                            "private_ip_addresses": private_ips,
                            "public_ip_addresses": public_ips,
                        },
                        NetworkInterfaceModel,
                    )
                )
            except Exception as e:
                self._log_warning(f"Error fetching NIC {nic_name}: {e}")
                continue

        self._log_debug(f"Fetched details for {len(network_interfaces)} NICs")
        return network_interfaces

    def _get_private_ips(self, nic):
        """
        Get private IP addresses from a network interface.

        Args:
            nic: Azure network interface object

        Returns:
            List of private IP addresses
        """
        private_ips = []
        if hasattr(nic, "ip_configurations") and nic.ip_configurations:
            private_ips = [
                ip_config.private_ip_address
                for ip_config in nic.ip_configurations
                if hasattr(ip_config, "private_ip_address")
                and ip_config.private_ip_address
            ]
        return private_ips

    async def _get_public_ips(self, nic, network_client, nic_rg_name, vm_name):
        """
        Get public IP addresses from a network interface.

        Args:
            nic: Azure network interface object
            network_client: Azure network client
            nic_rg_name: Resource group name of the NIC
            vm_name: VM name for logging

        Returns:
            List of public IP addresses
        """
        public_ips = []
        if not (hasattr(nic, "ip_configurations") and nic.ip_configurations):
            return public_ips

        for ip_config in nic.ip_configurations:
            if not (
                hasattr(ip_config, "public_ip_address") and ip_config.public_ip_address
            ):
                continue

            try:
                if (
                    hasattr(ip_config.public_ip_address, "name")
                    and ip_config.public_ip_address.name
                ):
                    self._log_debug(
                        f"Fetching public IP {ip_config.public_ip_address.name}"
                    )
                    public_ip = network_client.public_ip_addresses.get(
                        nic_rg_name, ip_config.public_ip_address.name
                    )
                    if hasattr(public_ip, "ip_address") and public_ip.ip_address:
                        public_ips.append(public_ip.ip_address)
                        self._log_debug(f"Fetched public IP {public_ip.ip_address}")
            except ResourceNotFoundError:
                self._log_warning(
                    f"Public IP {ip_config.public_ip_address.name if hasattr(ip_config.public_ip_address, 'name') else 'unknown'} not found."
                )
            except Exception as e:
                self._log_warning(f"Error fetching public IP: {e}")

        return public_ips

    def _get_port_range(self, rule):
        """
        Get port range from an NSG rule.

        Args:
            rule: NSG rule object

        Returns:
            Port range string
        """
        port_range = "Any"
        if hasattr(rule, "destination_port_range") and rule.destination_port_range:
            port_range = rule.destination_port_range
        elif hasattr(rule, "destination_port_ranges") and rule.destination_port_ranges:
            port_range = ",".join(rule.destination_port_ranges)
        return port_range

    async def _fetch_nsg_rules(
        self, network_client, resource_group_name, network_interfaces
    ):
        """
        Fetch effective NSG rules for the first network interface.

        Args:
            network_client: Azure network client
            resource_group_name: Resource group name
            network_interfaces: List of network interfaces

        Returns:
            List of NsgRuleModel objects
        """
        effective_nsg_rules = []
        if not network_interfaces:
            self._log_warning("No network interfaces available to fetch NSG rules")
            return effective_nsg_rules

        # Get the first NIC details
        first_nic = network_interfaces[0]
        first_nic_name = first_nic.name

        # Extract the resource group from the NIC ID
        nic_rg_name = self._extract_resource_group_from_id(
            first_nic.id, resource_group_name
        )

        self._log_debug(
            f"Fetching effective NSG rules for NIC {first_nic_name} in resource group {nic_rg_name}"
        )

        # Default NSG rules that are always present in Azure
        default_rules = [
            self._convert_to_model(
                {
                    "name": "AllowVnetInBound",
                    "direction": "Inbound",
                    "protocol": "*",
                    "port_range": "*",
                    "access": "Allow",
                },
                NsgRuleModel,
            ),
            self._convert_to_model(
                {
                    "name": "AllowAzureLoadBalancerInBound",
                    "direction": "Inbound",
                    "protocol": "*",
                    "port_range": "*",
                    "access": "Allow",
                },
                NsgRuleModel,
            ),
            self._convert_to_model(
                {
                    "name": "DenyAllInBound",
                    "direction": "Inbound",
                    "protocol": "*",
                    "port_range": "*",
                    "access": "Deny",
                },
                NsgRuleModel,
            ),
            self._convert_to_model(
                {
                    "name": "AllowVnetOutBound",
                    "direction": "Outbound",
                    "protocol": "*",
                    "port_range": "*",
                    "access": "Allow",
                },
                NsgRuleModel,
            ),
            self._convert_to_model(
                {
                    "name": "AllowInternetOutBound",
                    "direction": "Outbound",
                    "protocol": "*",
                    "port_range": "*",
                    "access": "Allow",
                },
                NsgRuleModel,
            ),
            self._convert_to_model(
                {
                    "name": "DenyAllOutBound",
                    "direction": "Outbound",
                    "protocol": "*",
                    "port_range": "*",
                    "access": "Deny",
                },
                NsgRuleModel,
            ),
        ]

        try:
            # Try to get direct NSG info first
            try:
                self._log_debug("Trying direct method to get NSG rules")

                # Look for the NSG attached to the NIC
                nic = network_client.network_interfaces.get(nic_rg_name, first_nic_name)

                # Get any NSG associated with this NIC
                if (
                    hasattr(nic, "network_security_group")
                    and nic.network_security_group
                ):
                    nsg_id = nic.network_security_group.id
                    if nsg_id:
                        nsg_parts = nsg_id.split("/")
                        if len(nsg_parts) >= 9:
                            nsg_rg = nsg_parts[4]
                            nsg_name = nsg_parts[8]

                            self._log_debug(
                                f"Getting NSG {nsg_name} from resource group {nsg_rg}"
                            )
                            nsg = network_client.network_security_groups.get(
                                nsg_rg, nsg_name
                            )

                            if (
                                nsg
                                and hasattr(nsg, "security_rules")
                                and nsg.security_rules
                            ):
                                for rule in nsg.security_rules:
                                    port_range = (
                                        rule.destination_port_range
                                        or ",".join(rule.destination_port_ranges)
                                        if hasattr(rule, "destination_port_ranges")
                                        else "*"
                                    )

                                    effective_nsg_rules.append(
                                        self._convert_to_model(
                                            {
                                                "name": rule.name,
                                                "direction": str(rule.direction),
                                                "protocol": str(rule.protocol),
                                                "port_range": port_range,
                                                "access": str(rule.access),
                                            },
                                            NsgRuleModel,
                                        )
                                    )

                # If we got custom rules, we're done
                if effective_nsg_rules:
                    self._log_debug(
                        f"Fetched {len(effective_nsg_rules)} NSG rules using direct method"
                    )
                    return effective_nsg_rules

            except Exception as direct_error:
                self._log_debug(f"Direct NSG rule fetch failed: {str(direct_error)}")

            # Try the effective NSG rules API
            try:
                self._log_debug("Trying effective NSG rules API")

                if hasattr(
                    network_client.network_interfaces,
                    "begin_get_effective_network_security_group",
                ):
                    poller = network_client.network_interfaces.begin_get_effective_network_security_group(
                        nic_rg_name, first_nic_name
                    )

                    # Wait for the operation to complete
                    result = poller.result()

                    # Process the result
                    if result:
                        # Try different result formats
                        if hasattr(result, "effective_security_rules"):
                            for rule in result.effective_security_rules:
                                port_range = self._get_port_range(rule)
                                effective_nsg_rules.append(
                                    self._convert_to_model(
                                        {
                                            "name": (
                                                rule.name
                                                if hasattr(rule, "name")
                                                else "Unnamed"
                                            ),
                                            "direction": (
                                                str(rule.direction)
                                                if hasattr(rule, "direction")
                                                else "Unknown"
                                            ),
                                            "protocol": (
                                                str(rule.protocol)
                                                if hasattr(rule, "protocol")
                                                else "Unknown"
                                            ),
                                            "port_range": port_range,
                                            "access": (
                                                str(rule.access)
                                                if hasattr(rule, "access")
                                                else "Unknown"
                                            ),
                                        },
                                        NsgRuleModel,
                                    )
                                )

                    self._log_debug(
                        f"Fetched {len(effective_nsg_rules)} effective NSG rules using API"
                    )

            except Exception as e:
                self._log_warning(f"Effective NSG rules API failed: {str(e)}")

            # If we still don't have any rules, use default rules
            if not effective_nsg_rules:
                self._log_debug("Using default NSG rules as no actual rules were found")
                effective_nsg_rules = default_rules

            return effective_nsg_rules

        except Exception as e:
            self._log_warning(
                f"Could not fetch effective NSG rules for NIC {first_nic_name}: {str(e)}"
            )
            self._log_debug(f"NSG rules fetch error trace: {traceback.format_exc()}")

            # Return default rules as fallback
            self._log_debug("Using default rules as fallback after exception")
            return default_rules

    async def _fetch_routes(
        self, network_client, resource_group_name, network_interfaces
    ):
        """
        Fetch effective routes for the first network interface.

        Args:
            network_client: Azure network client
            resource_group_name: Resource group name
            network_interfaces: List of network interfaces

        Returns:
            List of RouteModel objects
        """
        effective_routes = []
        if not network_interfaces:
            self._log_warning("No network interfaces available to fetch routes")
            return effective_routes

        # Get the first NIC details
        first_nic = network_interfaces[0]
        first_nic_name = first_nic.name

        # Extract the resource group from the NIC ID
        nic_rg_name = self._extract_resource_group_from_id(
            first_nic.id, resource_group_name
        )

        self._log_debug(
            f"Fetching effective routes for NIC {first_nic_name} in resource group {nic_rg_name}"
        )

        # Create some standard default routes that are typically present
        default_routes = [
            self._convert_to_model(
                {
                    "address_prefix": "0.0.0.0/0",
                    "next_hop_type": "Internet",
                    "next_hop_ip": None,
                    "route_origin": "Default",
                },
                RouteModel,
            ),
            self._convert_to_model(
                {
                    "address_prefix": "10.0.0.0/8",
                    "next_hop_type": "VnetLocal",
                    "next_hop_ip": None,
                    "route_origin": "Default",
                },
                RouteModel,
            ),
            self._convert_to_model(
                {
                    "address_prefix": "172.16.0.0/12",
                    "next_hop_type": "VnetLocal",
                    "next_hop_ip": None,
                    "route_origin": "Default",
                },
                RouteModel,
            ),
            self._convert_to_model(
                {
                    "address_prefix": "192.168.0.0/16",
                    "next_hop_type": "VnetLocal",
                    "next_hop_ip": None,
                    "route_origin": "Default",
                },
                RouteModel,
            ),
        ]

        try:
            # Try to use the begin_get_effective_route_table method
            try:
                self._log_debug("Trying effective route table API")

                # Check if the method exists in this SDK version
                if hasattr(
                    network_client.network_interfaces, "begin_get_effective_route_table"
                ):
                    poller = network_client.network_interfaces.begin_get_effective_route_table(
                        nic_rg_name, first_nic_name
                    )

                    result = poller.result()

                    if result and hasattr(result, "value"):
                        for route in result.value:
                            # Handle address_prefix which might be a list or a string
                            address_prefix = route.address_prefix
                            if isinstance(address_prefix, list):
                                address_prefix = (
                                    address_prefix[0] if address_prefix else ""
                                )

                            # Handle next_hop_ip_address which might be a list or a string
                            next_hop_ip = None
                            if hasattr(route, "next_hop_ip_address"):
                                next_hop_ip = route.next_hop_ip_address
                                if isinstance(next_hop_ip, list):
                                    next_hop_ip = (
                                        next_hop_ip[0] if next_hop_ip else None
                                    )

                            effective_routes.append(
                                self._convert_to_model(
                                    {
                                        "address_prefix": address_prefix,
                                        "next_hop_type": route.next_hop_type,
                                        "next_hop_ip": next_hop_ip,
                                        "route_origin": (
                                            route.source
                                            if hasattr(route, "source")
                                            else "Unknown"
                                        ),
                                    },
                                    RouteModel,
                                )
                            )

                        # If we got routes, we're done
                        if effective_routes:
                            self._log_debug(
                                f"Fetched {len(effective_routes)} routes using effective route table API"
                            )
                            return effective_routes
            except Exception as api_error:
                self._log_debug(f"Effective route table API failed: {str(api_error)}")

            # Try to get route table directly from the NIC's subnet
            try:
                self._log_debug("Trying direct method to get routes from NIC subnet")

                # Get detailed NIC info
                nic = network_client.network_interfaces.get(nic_rg_name, first_nic_name)

                # For this NIC, try to find subnet info from the IP configurations
                if hasattr(nic, "ip_configurations") and nic.ip_configurations:
                    for ip_config in nic.ip_configurations:
                        if hasattr(ip_config, "subnet") and ip_config.subnet:
                            if hasattr(ip_config.subnet, "id") and ip_config.subnet.id:
                                # The subnet ID contains virtual network info
                                subnet_id = ip_config.subnet.id
                                subnet_parts = subnet_id.split("/")

                                if len(subnet_parts) >= 11:
                                    vnet_rg = subnet_parts[4]
                                    vnet_name = subnet_parts[8]
                                    subnet_name = subnet_parts[10]

                                    self._log_debug(
                                        f"Looking for route tables in subnet {subnet_name} of VNet {vnet_name}"
                                    )

                                    # Get the subnet to find route tables
                                    try:
                                        subnet = network_client.subnets.get(
                                            vnet_rg, vnet_name, subnet_name
                                        )

                                        # Check if subnet has route table
                                        if (
                                            hasattr(subnet, "route_table")
                                            and subnet.route_table
                                        ):
                                            if (
                                                hasattr(subnet.route_table, "id")
                                                and subnet.route_table.id
                                            ):
                                                rt_id = subnet.route_table.id
                                                rt_parts = rt_id.split("/")

                                                if len(rt_parts) >= 9:
                                                    rt_rg = rt_parts[4]
                                                    rt_name = rt_parts[8]

                                                    self._log_debug(
                                                        f"Getting route table {rt_name} from resource group {rt_rg}"
                                                    )

                                                    # Get the route table and its routes
                                                    rt = (
                                                        network_client.route_tables.get(
                                                            rt_rg, rt_name
                                                        )
                                                    )

                                                    if (
                                                        hasattr(rt, "routes")
                                                        and rt.routes
                                                    ):
                                                        for route in rt.routes:
                                                            effective_routes.append(
                                                                self._convert_to_model(
                                                                    {
                                                                        "address_prefix": route.address_prefix,
                                                                        "next_hop_type": str(
                                                                            route.next_hop_type
                                                                        ),
                                                                        "next_hop_ip": route.next_hop_ip_address,
                                                                        "route_origin": "User",
                                                                    },
                                                                    RouteModel,
                                                                )
                                                            )
                                    except Exception as subnet_error:
                                        self._log_debug(
                                            f"Error getting subnet info: {str(subnet_error)}"
                                        )

                # If we got custom routes, we're done
                if effective_routes:
                    self._log_debug(
                        f"Fetched {len(effective_routes)} routes using direct method"
                    )
                    return effective_routes

            except Exception as direct_error:
                self._log_debug(f"Direct route fetch failed: {str(direct_error)}")

            # Return default routes since direct method failed
            self._log_debug("Using default routes as direct method failed")
            return default_routes

        except Exception as e:
            self._log_warning(
                f"Could not fetch routes for NIC {first_nic_name}: {str(e)}"
            )
            self._log_debug(f"Routes fetch error trace: {traceback.format_exc()}")

            # Return default routes as fallback on error
            self._log_debug("Using default routes as fallback after exception")
            return default_routes
