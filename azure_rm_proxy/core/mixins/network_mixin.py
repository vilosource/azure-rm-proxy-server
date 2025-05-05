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

    async def _fetch_network_interfaces(self, vm, network_client):
        """
        Fetch network interfaces for a VM.

        Args:
            vm: Azure VM object
            network_client: Azure network client

        Returns:
            List of NetworkInterfaceModel objects
        """
        network_interfaces = []
        if not (
            hasattr(vm, "network_profile")
            and vm.network_profile
            and hasattr(vm.network_profile, "network_interfaces")
        ):
            self._log_warning(f"VM {vm.name if hasattr(vm, 'name') else 'unknown'} does not have network interfaces defined")
            return network_interfaces

        for nic_ref in vm.network_profile.network_interfaces:
            if not nic_ref or not hasattr(nic_ref, "id") or not nic_ref.id:
                self._log_warning(f"NIC reference does not have an ID for VM {vm.name if hasattr(vm, 'name') else 'unknown'}")
                continue

            nic_id = nic_ref.id
            parts = nic_id.split("/")
            if len(parts) < 9:
                self._log_warning(f"Invalid NIC ID format: {nic_id}")
                continue

            nic_rg_name = parts[4]
            nic_name = parts[8]
            self._log_debug(f"Fetching NIC {nic_name} details")

            try:
                nic = network_client.network_interfaces.get(nic_rg_name, nic_name)
                private_ips = self._get_private_ips(nic)
                public_ips = await self._get_public_ips(
                    nic, network_client, nic_rg_name
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

    async def _get_public_ips(self, nic, network_client, nic_rg_name):
        """
        Get public IP addresses from a network interface.

        Args:
            nic: Azure network interface object
            network_client: Azure network client
            nic_rg_name: Resource group name of the NIC

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

    def _create_default_nsg_rules(self):
        """Create default NSG rules that are always present in Azure."""
        return [
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

    async def _fetch_rules_directly(self, network_client, nic_rg_name, nic_name):
        """
        Try to fetch NSG rules directly from the network interface.
        
        Args:
            network_client: Azure network client
            nic_rg_name: NIC's resource group name
            nic_name: Network interface name
        
        Returns:
            List of NSG rules if successful, empty list otherwise
        """
        rules = []
        try:
            self._log_debug("Trying direct method to get NSG rules")
            
            # Look for the NSG attached to the NIC
            nic = network_client.network_interfaces.get(nic_rg_name, nic_name)

            # Process only if the NIC has a network security group
            if not (hasattr(nic, "network_security_group") and nic.network_security_group):
                return []
                
            nsg_id = nic.network_security_group.id
            if not nsg_id:
                return []
                
            nsg_parts = nsg_id.split("/")
            if len(nsg_parts) < 9:
                return []
                
            nsg_rg = nsg_parts[4]
            nsg_name = nsg_parts[8]

            self._log_debug(f"Getting NSG {nsg_name} from resource group {nsg_rg}")
            nsg = network_client.network_security_groups.get(nsg_rg, nsg_name)

            if not (nsg and hasattr(nsg, "security_rules") and nsg.security_rules):
                return []
                
            for rule in nsg.security_rules:
                port_range = (
                    rule.destination_port_range
                    or ",".join(rule.destination_port_ranges)
                    if hasattr(rule, "destination_port_ranges")
                    else "*"
                )

                rules.append(
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
                
            self._log_debug(f"Fetched {len(rules)} NSG rules using direct method")
        except Exception as direct_error:
            self._log_debug(f"Direct NSG rule fetch failed: {str(direct_error)}")
            
        return rules
        
    async def _fetch_rules_via_api(self, network_client, nic_rg_name, nic_name):
        """
        Try to fetch NSG rules using the effective network security group API.
        
        Args:
            network_client: Azure network client
            nic_rg_name: NIC's resource group name
            nic_name: Network interface name
        
        Returns:
            List of NSG rules if successful, empty list otherwise
        """
        rules = []
        try:
            self._log_debug("Trying effective NSG rules API")

            if not hasattr(network_client.network_interfaces, "begin_get_effective_network_security_group"):
                return []
                
            poller = network_client.network_interfaces.begin_get_effective_network_security_group(
                nic_rg_name, nic_name
            )

            # Wait for the operation to complete
            result = poller.result()

            # Process the result if available
            if not (result and hasattr(result, "effective_security_rules")):
                return []
                
            for rule in result.effective_security_rules:
                port_range = self._get_port_range(rule)
                rules.append(
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

            self._log_debug(f"Fetched {len(rules)} effective NSG rules using API")
        except Exception as e:
            self._log_warning(f"Effective NSG rules API failed: {str(e)}")
            
        return rules

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
        # Early return if no network interfaces are available
        if not network_interfaces:
            self._log_warning("No network interfaces available to fetch NSG rules")
            return []

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

        # Default rules to use if no specific rules are found
        default_rules = self._create_default_nsg_rules()

        try:
            # First attempt: Try to get direct NSG info
            direct_rules = await self._fetch_rules_directly(network_client, nic_rg_name, first_nic_name)
            if direct_rules:
                return direct_rules

            # Second attempt: Try the effective NSG rules API
            api_rules = await self._fetch_rules_via_api(network_client, nic_rg_name, first_nic_name)
            if api_rules:
                return api_rules

            # If we still don't have any rules, use default rules
            self._log_debug("Using default NSG rules as no actual rules were found")
            return default_rules

        except Exception as e:
            self._log_warning(
                f"Could not fetch effective NSG rules for NIC {first_nic_name}: {str(e)}"
            )
            self._log_debug(f"NSG rules fetch error trace: {traceback.format_exc()}")

            # Return default rules as fallback
            self._log_debug("Using default rules as fallback after exception")
            return default_rules

    def _create_default_routes(self):
        """Create standard default routes that are typically present in Azure."""
        return [
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
    
    async def _fetch_routes_via_api(self, network_client, nic_rg_name, nic_name):
        """
        Try to fetch routes using the effective route table API.
        
        Args:
            network_client: Azure network client
            nic_rg_name: NIC's resource group name
            nic_name: Network interface name
        
        Returns:
            List of routes if successful, empty list otherwise
        """
        routes = []
        try:
            self._log_debug("Trying effective route table API")

            # Check if the method exists in this SDK version
            if not hasattr(network_client.network_interfaces, "begin_get_effective_route_table"):
                return []
                
            poller = network_client.network_interfaces.begin_get_effective_route_table(
                nic_rg_name, nic_name
            )

            result = poller.result()
            if not (result and hasattr(result, "value")):
                return []

            for route in result.value:
                # Handle address_prefix which might be a list or a string
                address_prefix = route.address_prefix
                if isinstance(address_prefix, list):
                    address_prefix = address_prefix[0] if address_prefix else ""

                # Handle next_hop_ip_address which might be a list or a string
                next_hop_ip = None
                if hasattr(route, "next_hop_ip_address"):
                    next_hop_ip = route.next_hop_ip_address
                    if isinstance(next_hop_ip, list):
                        next_hop_ip = next_hop_ip[0] if next_hop_ip else None

                routes.append(
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

            self._log_debug(f"Fetched {len(routes)} routes using effective route table API")
        except Exception as api_error:
            self._log_debug(f"Effective route table API failed: {str(api_error)}")
            
        return routes
    
    async def _fetch_subnet_route_table(self, network_client, subnet, subnet_parts):
        """
        Extract and fetch route table info from a subnet object.
        
        Args:
            network_client: Azure network client
            subnet: Azure subnet object
            subnet_parts: Parts of the subnet ID path
            
        Returns:
            List of routes if successful, empty list otherwise
        """
        routes = []
        
        if not (hasattr(subnet, "route_table") and subnet.route_table):
            return []
            
        if not (hasattr(subnet.route_table, "id") and subnet.route_table.id):
            return []
            
        rt_id = subnet.route_table.id
        rt_parts = rt_id.split("/")

        if len(rt_parts) < 9:
            return []
            
        rt_rg = rt_parts[4]
        rt_name = rt_parts[8]

        self._log_debug(f"Getting route table {rt_name} from resource group {rt_rg}")

        # Get the route table and its routes
        try:
            rt = network_client.route_tables.get(rt_rg, rt_name)

            if not (hasattr(rt, "routes") and rt.routes):
                return []
                
            for route in rt.routes:
                routes.append(
                    self._convert_to_model(
                        {
                            "address_prefix": route.address_prefix,
                            "next_hop_type": str(route.next_hop_type),
                            "next_hop_ip": route.next_hop_ip_address,
                            "route_origin": "User",
                        },
                        RouteModel,
                    )
                )
        except Exception as rt_error:
            self._log_debug(f"Error getting route table: {str(rt_error)}")
            
        return routes
    
    async def _fetch_routes_from_subnet(self, network_client, nic_rg_name, nic_name):
        """
        Try to get route table directly from the NIC's subnet.
        
        Args:
            network_client: Azure network client
            nic_rg_name: NIC's resource group name
            nic_name: Network interface name
        
        Returns:
            List of routes if successful, empty list otherwise
        """
        routes = []
        try:
            self._log_debug("Trying direct method to get routes from NIC subnet")

            # Get detailed NIC info
            nic = network_client.network_interfaces.get(nic_rg_name, nic_name)

            # For this NIC, try to find subnet info from the IP configurations
            if not (hasattr(nic, "ip_configurations") and nic.ip_configurations):
                return []
                
            for ip_config in nic.ip_configurations:
                if not (hasattr(ip_config, "subnet") and ip_config.subnet):
                    continue
                    
                if not (hasattr(ip_config.subnet, "id") and ip_config.subnet.id):
                    continue
                    
                # The subnet ID contains virtual network info
                subnet_id = ip_config.subnet.id
                subnet_parts = subnet_id.split("/")

                if len(subnet_parts) < 11:
                    continue
                    
                vnet_rg = subnet_parts[4]
                vnet_name = subnet_parts[8]
                subnet_name = subnet_parts[10]

                self._log_debug(f"Looking for route tables in subnet {subnet_name} of VNet {vnet_name}")

                # Get the subnet to find route tables
                try:
                    subnet = network_client.subnets.get(vnet_rg, vnet_name, subnet_name)
                    subnet_routes = await self._fetch_subnet_route_table(network_client, subnet, subnet_parts)
                    routes.extend(subnet_routes)
                except Exception as subnet_error:
                    self._log_debug(f"Error getting subnet info: {str(subnet_error)}")

            if routes:
                self._log_debug(f"Fetched {len(routes)} routes using direct method")
        except Exception as direct_error:
            self._log_debug(f"Direct route fetch failed: {str(direct_error)}")
            
        return routes

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
        # Early return if no network interfaces are available
        if not network_interfaces:
            self._log_warning("No network interfaces available to fetch routes")
            return []

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

        # Default routes to use if no specific routes are found
        default_routes = self._create_default_routes()

        try:
            # First attempt: Try to use the begin_get_effective_route_table method
            api_routes = await self._fetch_routes_via_api(network_client, nic_rg_name, first_nic_name)
            if api_routes:
                return api_routes

            # Second attempt: Try to get route table directly from the NIC's subnet
            direct_routes = await self._fetch_routes_from_subnet(network_client, nic_rg_name, first_nic_name)
            if direct_routes:
                return direct_routes

            # If both methods failed, return default routes
            self._log_debug("Using default routes as both fetch methods failed")
            return default_routes

        except Exception as e:
            self._log_warning(
                f"Could not fetch routes for NIC {first_nic_name}: {str(e)}"
            )
            self._log_debug(f"Routes fetch error trace: {traceback.format_exc()}")

            # Return default routes as fallback on error
            self._log_debug("Using default routes as fallback after exception")
            return default_routes
