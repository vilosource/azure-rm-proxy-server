"""Route table functionality mixin for Azure Resource Service."""

import logging
from typing import List, Optional

from azure.core.exceptions import ResourceNotFoundError, ClientAuthenticationError

from ..azure_clients import AzureClientFactory
from ..models import RouteTableSummaryModel, RouteTableModel, RouteEntryModel, RouteModel
from .base_mixin import BaseAzureResourceMixin
from ...app.config import settings

logger = logging.getLogger(__name__)


class RouteMixin(BaseAzureResourceMixin):
    """Mixin for route table-related operations."""

    async def get_route_tables(
        self,
        subscription_id: str,
        refresh_cache: bool = False
    ) -> List[RouteTableSummaryModel]:
        """
        Get all route tables for a subscription.

        Args:
            subscription_id: Azure subscription ID
            refresh_cache: Whether to refresh the cache

        Returns:
            List of route table summary models
        """
        cache_key = self._get_cache_key(["route_tables", subscription_id])
        self._log_debug(
            f"Attempting to get route tables for subscription {subscription_id} with refresh_cache={refresh_cache}"
        )

        if not refresh_cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                self._log_debug(
                    f"Cache hit for route tables in subscription {subscription_id}"
                )
                return self._validate_cached_data(cached_data, RouteTableSummaryModel)

        self._log_info(
            f"Fetching route tables for subscription {subscription_id} from Azure"
        )
        try:
            network_client = AzureClientFactory.create_network_client(
                subscription_id, self.credential
            )

            async with self.limiter:
                self._log_debug(
                    f"Acquired concurrency limiter for route tables in subscription {subscription_id}"
                )

                route_tables = []
                for rt in network_client.route_tables.list_all():
                    # Extract resource group from the ID
                    resource_group = self._extract_resource_group_from_id(rt.id, "unknown")
                    
                    # Count routes and subnets
                    route_count = len(rt.routes) if rt.routes else 0
                    subnet_count = len(rt.subnets) if rt.subnets else 0
                    
                    rt_summary = RouteTableSummaryModel(
                        id=rt.id,
                        name=rt.name,
                        location=rt.location,
                        resource_group=resource_group,
                        route_count=route_count,
                        subnet_count=subnet_count,
                        provisioning_state=rt.provisioning_state,
                        subscription_id=subscription_id,
                    )
                    route_tables.append(rt_summary)

                self._log_debug(
                    f"Released concurrency limiter for route tables in subscription {subscription_id}"
                )

            self._set_cache_with_ttl(cache_key, route_tables, settings.cache_ttl)
            self._log_info(
                f"Fetched {len(route_tables)} route tables for subscription {subscription_id}"
            )
            return route_tables

        except ResourceNotFoundError as e:
            self._log_warning(f"Subscription {subscription_id} not found: {e}")
            raise
        except ClientAuthenticationError as e:
            self._log_error(f"Authentication error fetching route tables: {e}")
            raise
        except Exception as e:
            self._log_error(
                f"Error fetching route tables for subscription {subscription_id}: {e}"
            )
            raise

    async def get_route_table_details(
        self,
        subscription_id: str,
        resource_group_name: str,
        route_table_name: str,
        refresh_cache: bool = False
    ) -> RouteTableModel:
        """
        Get detailed information about a route table.

        Args:
            subscription_id: Azure subscription ID
            resource_group_name: Resource group name
            route_table_name: Route table name
            refresh_cache: Whether to refresh the cache

        Returns:
            Route table detail model
        """
        cache_key = self._get_cache_key(
            ["route_table", subscription_id, resource_group_name, route_table_name]
        )
        self._log_debug(
            f"Attempting to get route table details for {route_table_name} in {resource_group_name} with refresh_cache={refresh_cache}"
        )

        if not refresh_cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                self._log_debug(f"Cache hit for route table details of {route_table_name}")
                return self._validate_cached_data(cached_data, RouteTableModel)

        self._log_info(
            f"Fetching route table details for {route_table_name} in resource group {resource_group_name} from Azure"
        )

        try:
            network_client = AzureClientFactory.create_network_client(
                subscription_id, self.credential
            )

            async with self.limiter:
                self._log_debug(
                    f"Acquired concurrency limiter for route table details of {route_table_name}"
                )

                rt = network_client.route_tables.get(resource_group_name, route_table_name)
                
                # Convert routes to model
                routes = []
                if rt.routes:
                    for route in rt.routes:
                        route_entry = RouteEntryModel(
                            name=route.name,
                            address_prefix=route.address_prefix,
                            next_hop_type=route.next_hop_type,
                            next_hop_ip_address=route.next_hop_ip_address
                        )
                        routes.append(route_entry)
                
                # Extract subnet references
                subnets = []
                if rt.subnets:
                    for subnet in rt.subnets:
                        subnets.append(subnet.id)
                
                # Create the detailed model
                route_table = RouteTableModel(
                    id=rt.id,
                    name=rt.name,
                    location=rt.location,
                    resource_group=resource_group_name,
                    routes=routes,
                    subnets=subnets,
                    provisioning_state=rt.provisioning_state,
                    disable_bgp_route_propagation=rt.disable_bgp_route_propagation if hasattr(rt, 'disable_bgp_route_propagation') else False,
                    tags=rt.tags,
                    subscription_id=subscription_id
                )

                self._log_debug(
                    f"Released concurrency limiter for route table details of {route_table_name}"
                )

            self._set_cache_with_ttl(cache_key, route_table, settings.cache_ttl)
            self._log_info(
                f"Successfully fetched and cached route table details for {route_table_name}"
            )
            return route_table

        except ResourceNotFoundError as e:
            self._log_warning(
                f"Route table {route_table_name} not found in resource group {resource_group_name}: {e}"
            )
            raise
        except ClientAuthenticationError as e:
            self._log_error(f"Authentication error fetching route table details: {e}")
            raise
        except Exception as e:
            self._log_error(f"Error fetching route table details for {route_table_name}: {e}")
            raise

    async def get_vm_effective_routes(
        self,
        subscription_id: str,
        resource_group_name: str,
        vm_name: str,
        refresh_cache: bool = False
    ) -> List[RouteModel]:
        """
        Get effective routes for a virtual machine.

        Args:
            subscription_id: Azure subscription ID
            resource_group_name: Resource group name
            vm_name: Virtual machine name
            refresh_cache: Whether to refresh the cache

        Returns:
            List of effective route models
        """
        cache_key = self._get_cache_key(
            ["vm_routes", subscription_id, resource_group_name, vm_name]
        )
        self._log_debug(
            f"Attempting to get effective routes for VM {vm_name} with refresh_cache={refresh_cache}"
        )

        if not refresh_cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                self._log_debug(f"Cache hit for effective routes of VM {vm_name}")
                return self._validate_cached_data(cached_data, RouteModel)

        self._log_info(
            f"Fetching effective routes for VM {vm_name} in resource group {resource_group_name} from Azure"
        )

        try:
            # Reuse the `get_vm_details` method to fetch VM details with caching
            vm_details = await self.get_vm_details(
                subscription_id,
                resource_group_name,
                vm_name,
                refresh_cache=refresh_cache
            )

            # Extract network interfaces from the VM details
            nic_ids = [nic.id for nic in vm_details.network_interfaces]

            self._log_debug(f"Found {len(nic_ids)} network interfaces for VM {vm_name}")

            # Get effective routes for each network interface
            all_effective_routes = []
            
            for nic_id in nic_ids:
                # Extract resource group and nic name from the ID
                nic_name = nic_id.split('/')[-1]
                nic_resource_group = self._extract_resource_group_from_id(nic_id)
                
                self._log_debug(f"Getting effective routes for NIC {nic_name}")
                
                # Get the effective routes for this NIC
                try:
                    nic_routes = await self.get_nic_effective_routes(
                        subscription_id, nic_resource_group, nic_name, refresh_cache=refresh_cache
                    )
                    all_effective_routes.extend(nic_routes)
                except Exception as e:
                    self._log_warning(f"Error getting routes for NIC {nic_name}: {e}")
                    continue

            # Remove duplicates based on address prefix and next hop type
            unique_routes = {}
            for route in all_effective_routes:
                key = f"{route.address_prefix}|{route.next_hop_type}|{route.next_hop_ip}"
                unique_routes[key] = route
            
            result = list(unique_routes.values())
            
            self._set_cache_with_ttl(cache_key, result, settings.cache_ttl)
            self._log_info(
                f"Successfully fetched and cached {len(result)} effective routes for VM {vm_name}"
            )
            return result

        except ResourceNotFoundError as e:
            self._log_warning(
                f"VM {vm_name} not found in resource group {resource_group_name}: {e}"
            )
            raise
        except ClientAuthenticationError as e:
            self._log_error(f"Authentication error fetching VM effective routes: {e}")
            raise
        except Exception as e:
            self._log_error(f"Error fetching effective routes for VM {vm_name}: {e}")
            raise

    async def get_nic_effective_routes(
        self,
        subscription_id: str,
        resource_group_name: str,
        nic_name: str,
        refresh_cache: bool = False
    ) -> List[RouteModel]:
        """
        Get effective routes for a network interface.

        Args:
            subscription_id: Azure subscription ID
            resource_group_name: Resource group name
            nic_name: Network interface name
            refresh_cache: Whether to refresh the cache

        Returns:
            List of effective route models
        """
        cache_key = self._get_cache_key(
            ["nic_routes", subscription_id, resource_group_name, nic_name]
        )
        self._log_debug(
            f"Attempting to get effective routes for NIC {nic_name} with refresh_cache={refresh_cache}"
        )

        if not refresh_cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                self._log_debug(f"Cache hit for effective routes of NIC {nic_name}")
                return self._validate_cached_data(cached_data, RouteModel)

        self._log_info(
            f"Fetching effective routes for NIC {nic_name} in resource group {resource_group_name} from Azure"
        )

        try:
            network_client = AzureClientFactory.create_network_client(
                subscription_id, self.credential
            )

            async with self.limiter:
                self._log_debug(
                    f"Acquired concurrency limiter for NIC {nic_name} effective routes"
                )
                
                effective_routes = []
                
                # Directly fetch effective routes using the begin_ method
                self._log_debug(f"Calling begin_get_effective_route_table for NIC {nic_name}")
                poller = network_client.network_interfaces.begin_get_effective_route_table(
                    resource_group_name, nic_name
                )
                
                # Get the result from the poller
                self._log_debug(f"Waiting for result from effective route table poller for NIC {nic_name}")
                effective_routes_result = poller.result()
                
                # Process the routes if they exist
                if effective_routes_result and hasattr(effective_routes_result, 'value') and effective_routes_result.value:
                    self._log_debug(f"Found {len(effective_routes_result.value)} routes for NIC {nic_name}")
                    for route in effective_routes_result.value:
                        # Handle address_prefix which might be a list or a string
                        address_prefix = route.address_prefix
                        if isinstance(address_prefix, list):
                            address_prefix = address_prefix[0] if address_prefix else ""
                            self._log_debug(f"Converted address_prefix from list to string: {address_prefix}")
                        
                        # Handle next_hop_ip_address which might be a list or a string
                        next_hop_ip = None
                        if hasattr(route, 'next_hop_ip_address'):
                            next_hop_ip = route.next_hop_ip_address
                            if isinstance(next_hop_ip, list):
                                next_hop_ip = next_hop_ip[0] if next_hop_ip else None
                                self._log_debug(f"Converted next_hop_ip from list to string: {next_hop_ip}")
                        
                        route_model = RouteModel(
                            address_prefix=address_prefix,
                            next_hop_type=route.next_hop_type,
                            next_hop_ip=next_hop_ip,
                            route_origin=route.source if hasattr(route, 'source') else "Unknown"
                        )
                        effective_routes.append(route_model)
                else:
                    self._log_debug(f"No effective routes found for NIC {nic_name}")

                self._log_debug(
                    f"Released concurrency limiter for NIC {nic_name} effective routes"
                )

            self._set_cache_with_ttl(cache_key, effective_routes, settings.cache_ttl)
            self._log_info(
                f"Successfully fetched and cached {len(effective_routes)} effective routes for NIC {nic_name}"
            )
            return effective_routes

        except ResourceNotFoundError as e:
            self._log_warning(
                f"NIC {nic_name} not found in resource group {resource_group_name}: {e}"
            )
            raise
        except ClientAuthenticationError as e:
            self._log_error(f"Authentication error fetching NIC effective routes: {e}")
            raise
        except Exception as e:
            self._log_error(f"Error fetching effective routes for NIC {nic_name}: {e}")
            raise