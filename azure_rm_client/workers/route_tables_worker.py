from .worker_base import Worker
import requests
import logging

logger = logging.getLogger(__name__)

class RouteTablesWorker(Worker):
    """
    Worker for handling operations related to route tables.
    """
    def __init__(self, base_url="http://localhost:8000"):
        """
        Initialize the RouteTablesWorker with a base URL.
        
        Args:
            base_url (str): The base URL for the Azure RM Proxy Server.
        """
        self.base_url = base_url

    def list_route_tables(self, subscription_id: str, refresh_cache: bool = False):
        """
        List all route tables for a specific subscription.
        
        Args:
            subscription_id (str): The ID of the subscription.
            refresh_cache (bool): Whether to bypass cache and fetch fresh data.
            
        Returns:
            list: A list of route table summary models.
        """
        endpoint = f"{self.base_url}/api/subscriptions/{subscription_id}/routetables"
        params = {"refresh-cache": refresh_cache}
        
        try:
            logger.debug(f"Fetching route tables for subscription {subscription_id}")
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            route_tables = response.json()
            logger.debug(f"Fetched {len(route_tables)} route tables for subscription {subscription_id}")
            return route_tables
        except requests.RequestException as e:
            logger.error(f"Failed to fetch route tables for subscription {subscription_id}: {e}")
            raise

    def get_route_table_details(self, subscription_id: str, resource_group_name: str, 
                               route_table_name: str, refresh_cache: bool = False):
        """
        Get detailed information about a specific route table.
        
        Args:
            subscription_id (str): The ID of the subscription.
            resource_group_name (str): The name of the resource group.
            route_table_name (str): The name of the route table.
            refresh_cache (bool): Whether to bypass cache and fetch fresh data.
            
        Returns:
            dict: Details of the route table.
        """
        endpoint = f"{self.base_url}/api/subscriptions/{subscription_id}/resourcegroups/{resource_group_name}/routetables/{route_table_name}"
        params = {"refresh-cache": refresh_cache}
        
        try:
            logger.debug(f"Fetching details for route table {route_table_name} in resource group {resource_group_name}")
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            route_table_details = response.json()
            logger.debug(f"Fetched details for route table {route_table_name}")
            return route_table_details
        except requests.RequestException as e:
            logger.error(f"Failed to fetch details for route table {route_table_name}: {e}")
            raise

    def get_vm_effective_routes(self, subscription_id: str, resource_group_name: str, 
                               vm_name: str, refresh_cache: bool = False):
        """
        Get all effective routes for a specific virtual machine.
        
        Args:
            subscription_id (str): The ID of the subscription.
            resource_group_name (str): The name of the resource group.
            vm_name (str): The name of the virtual machine.
            refresh_cache (bool): Whether to bypass cache and fetch fresh data.
            
        Returns:
            list: A list of effective routes.
        """
        endpoint = f"{self.base_url}/api/subscriptions/{subscription_id}/resourcegroups/{resource_group_name}/virtualmachines/{vm_name}/routes"
        params = {"refresh-cache": refresh_cache}
        
        try:
            logger.debug(f"Fetching effective routes for VM {vm_name} in resource group {resource_group_name}")
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            vm_routes = response.json()
            logger.debug(f"Fetched {len(vm_routes)} effective routes for VM {vm_name}")
            return vm_routes
        except requests.RequestException as e:
            logger.error(f"Failed to fetch effective routes for VM {vm_name}: {e}")
            raise

    def get_nic_effective_routes(self, subscription_id: str, resource_group_name: str, 
                                nic_name: str, refresh_cache: bool = False):
        """
        Get all effective routes for a specific network interface.
        
        Args:
            subscription_id (str): The ID of the subscription.
            resource_group_name (str): The name of the resource group.
            nic_name (str): The name of the network interface.
            refresh_cache (bool): Whether to bypass cache and fetch fresh data.
            
        Returns:
            list: A list of effective routes.
        """
        endpoint = f"{self.base_url}/api/subscriptions/{subscription_id}/resourcegroups/{resource_group_name}/networkinterfaces/{nic_name}/routes"
        params = {"refresh-cache": refresh_cache}
        
        try:
            logger.debug(f"Fetching effective routes for NIC {nic_name} in resource group {resource_group_name}")
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            nic_routes = response.json()
            logger.debug(f"Fetched {len(nic_routes)} effective routes for NIC {nic_name}")
            return nic_routes
        except requests.RequestException as e:
            logger.error(f"Failed to fetch effective routes for NIC {nic_name}: {e}")
            raise

    def execute(self, *args, **kwargs):
        """
        Execute the worker's task based on provided arguments.
        
        Supported operation types:
        - list_route_tables: List all route tables for a subscription
        - get_route_table_details: Get detailed information about a specific route table
        - get_vm_effective_routes: Get effective routes for a VM
        - get_nic_effective_routes: Get effective routes for a NIC
        
        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
                - operation (str): The operation to perform.
                - Other parameters specific to each operation.
        
        Returns:
            Result of the requested operation.
        """
        operation = kwargs.get('operation', 'list_route_tables')
        
        if operation == 'list_route_tables':
            subscription_id = kwargs.get('subscription_id')
            refresh_cache = kwargs.get('refresh_cache', False)
            if not subscription_id:
                raise ValueError("subscription_id is required for list_route_tables operation")
            return self.list_route_tables(subscription_id, refresh_cache)
            
        elif operation == 'get_route_table_details':
            subscription_id = kwargs.get('subscription_id')
            resource_group_name = kwargs.get('resource_group_name')
            route_table_name = kwargs.get('route_table_name')
            refresh_cache = kwargs.get('refresh_cache', False)
            
            if not all([subscription_id, resource_group_name, route_table_name]):
                raise ValueError("subscription_id, resource_group_name, and route_table_name are required for get_route_table_details operation")
                
            return self.get_route_table_details(subscription_id, resource_group_name, route_table_name, refresh_cache)
            
        elif operation == 'get_vm_effective_routes':
            subscription_id = kwargs.get('subscription_id')
            resource_group_name = kwargs.get('resource_group_name')
            vm_name = kwargs.get('vm_name')
            refresh_cache = kwargs.get('refresh_cache', False)
            
            if not all([subscription_id, resource_group_name, vm_name]):
                raise ValueError("subscription_id, resource_group_name, and vm_name are required for get_vm_effective_routes operation")
                
            return self.get_vm_effective_routes(subscription_id, resource_group_name, vm_name, refresh_cache)
            
        elif operation == 'get_nic_effective_routes':
            subscription_id = kwargs.get('subscription_id')
            resource_group_name = kwargs.get('resource_group_name')
            nic_name = kwargs.get('nic_name')
            refresh_cache = kwargs.get('refresh_cache', False)
            
            if not all([subscription_id, resource_group_name, nic_name]):
                raise ValueError("subscription_id, resource_group_name, and nic_name are required for get_nic_effective_routes operation")
                
            return self.get_nic_effective_routes(subscription_id, resource_group_name, nic_name, refresh_cache)
            
        else:
            raise ValueError(f"Unsupported operation: {operation}")