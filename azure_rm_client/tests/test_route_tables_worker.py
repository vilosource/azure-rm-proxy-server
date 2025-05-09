import pytest
from unittest.mock import patch, MagicMock
import requests # For requests.exceptions

from azure_rm_client.workers.route_tables_worker import RouteTablesWorker

# Patch the module-level logger used by the worker
@patch('azure_rm_client.workers.route_tables_worker.logger', new_callable=MagicMock)
class TestRouteTablesWorker:
    """Tests for the RouteTablesWorker class."""

    DEFAULT_BASE_URL = "http://localhost:8000"
    SUBSCRIPTION_ID = "test-sub-id"
    RESOURCE_GROUP_NAME = "test-rg"
    ROUTE_TABLE_NAME = "test-rt-name"
    VM_NAME = "test-vm"
    NIC_NAME = "test-nic"

    @pytest.fixture
    def worker(self):
        """Fixture to create a RouteTablesWorker instance."""
        return RouteTablesWorker(base_url=self.DEFAULT_BASE_URL)

    def _mock_response(self, json_data, status_code=200, raise_for_status_effect=None):
        mock_resp = MagicMock()
        mock_resp.status_code = status_code
        mock_resp.json.return_value = json_data
        if raise_for_status_effect:
            mock_resp.raise_for_status.side_effect = raise_for_status_effect
        else:
            mock_resp.raise_for_status = MagicMock()
        return mock_resp

    # Tests for list_route_tables
    def test_list_route_tables_success(self, mock_logger, worker):
        expected_data = [{"name": "rt1"}, {"name": "rt2"}]
        mock_response = self._mock_response(json_data=expected_data)
        
        with patch("requests.get", return_value=mock_response) as mock_get:
            result = worker.list_route_tables(self.SUBSCRIPTION_ID, refresh_cache=False)

        assert result == expected_data
        expected_url = f"{self.DEFAULT_BASE_URL}/api/subscriptions/{self.SUBSCRIPTION_ID}/routetables"
        mock_get.assert_called_once_with(expected_url, params={"refresh-cache": False})
        mock_logger.debug.assert_any_call(f"Fetching route tables for subscription {self.SUBSCRIPTION_ID}")
        mock_logger.debug.assert_any_call(f"Fetched {len(expected_data)} route tables for subscription {self.SUBSCRIPTION_ID}")

    def test_list_route_tables_with_refresh_cache(self, mock_logger, worker):
        mock_response = self._mock_response(json_data=[])
        with patch("requests.get", return_value=mock_response) as mock_get:
            worker.list_route_tables(self.SUBSCRIPTION_ID, refresh_cache=True)
        
        expected_url = f"{self.DEFAULT_BASE_URL}/api/subscriptions/{self.SUBSCRIPTION_ID}/routetables"
        mock_get.assert_called_once_with(expected_url, params={"refresh-cache": True})

    def test_list_route_tables_http_error(self, mock_logger, worker):
        error = requests.exceptions.HTTPError("API Error")
        mock_response = self._mock_response(json_data={}, raise_for_status_effect=error)
        
        with patch("requests.get", return_value=mock_response) as mock_get:
            with pytest.raises(requests.exceptions.HTTPError, match="API Error"):
                worker.list_route_tables(self.SUBSCRIPTION_ID)
        
        mock_logger.error.assert_called_once_with(f"Failed to fetch route tables for subscription {self.SUBSCRIPTION_ID}: API Error")

    # Tests for get_route_table_details
    def test_get_route_table_details_success(self, mock_logger, worker):
        expected_details = {"id": "rt-detail-id", "name": self.ROUTE_TABLE_NAME}
        mock_response = self._mock_response(json_data=expected_details)

        with patch("requests.get", return_value=mock_response) as mock_get:
            result = worker.get_route_table_details(
                self.SUBSCRIPTION_ID, self.RESOURCE_GROUP_NAME, self.ROUTE_TABLE_NAME, refresh_cache=False
            )
        
        assert result == expected_details
        expected_url = f"{self.DEFAULT_BASE_URL}/api/subscriptions/{self.SUBSCRIPTION_ID}/resourcegroups/{self.RESOURCE_GROUP_NAME}/routetables/{self.ROUTE_TABLE_NAME}"
        mock_get.assert_called_once_with(expected_url, params={"refresh-cache": False})
        mock_logger.debug.assert_any_call(f"Fetching details for route table {self.ROUTE_TABLE_NAME} in resource group {self.RESOURCE_GROUP_NAME}")
        mock_logger.debug.assert_any_call(f"Fetched details for route table {self.ROUTE_TABLE_NAME}")

    def test_get_route_table_details_http_error(self, mock_logger, worker):
        error = requests.exceptions.RequestException("Network Error")
        mock_response = self._mock_response(json_data={}, raise_for_status_effect=error)

        with patch("requests.get", return_value=mock_response) as mock_get:
            with pytest.raises(requests.exceptions.RequestException, match="Network Error"):
                worker.get_route_table_details(self.SUBSCRIPTION_ID, self.RESOURCE_GROUP_NAME, self.ROUTE_TABLE_NAME)
        
        mock_logger.error.assert_called_once_with(f"Failed to fetch details for route table {self.ROUTE_TABLE_NAME}: Network Error")

    # Tests for get_vm_effective_routes
    def test_get_vm_effective_routes_success(self, mock_logger, worker):
        expected_routes = [{"route": "vm-route1"}]
        mock_response = self._mock_response(json_data=expected_routes)

        with patch("requests.get", return_value=mock_response) as mock_get:
            result = worker.get_vm_effective_routes(
                self.SUBSCRIPTION_ID, self.RESOURCE_GROUP_NAME, self.VM_NAME, refresh_cache=True
            )

        assert result == expected_routes
        expected_url = f"{self.DEFAULT_BASE_URL}/api/subscriptions/{self.SUBSCRIPTION_ID}/resourcegroups/{self.RESOURCE_GROUP_NAME}/virtualmachines/{self.VM_NAME}/routes"
        mock_get.assert_called_once_with(expected_url, params={"refresh-cache": True})
        mock_logger.debug.assert_any_call(f"Fetching effective routes for VM {self.VM_NAME} in resource group {self.RESOURCE_GROUP_NAME}")
        mock_logger.debug.assert_any_call(f"Fetched {len(expected_routes)} effective routes for VM {self.VM_NAME}")

    def test_get_vm_effective_routes_http_error(self, mock_logger, worker):
        error = requests.exceptions.HTTPError("VM Route Error")
        mock_response = self._mock_response(json_data={}, raise_for_status_effect=error)

        with patch("requests.get", return_value=mock_response) as mock_get:
            with pytest.raises(requests.exceptions.HTTPError, match="VM Route Error"):
                worker.get_vm_effective_routes(self.SUBSCRIPTION_ID, self.RESOURCE_GROUP_NAME, self.VM_NAME)
        
        mock_logger.error.assert_called_once_with(f"Failed to fetch effective routes for VM {self.VM_NAME}: VM Route Error")

    # Tests for get_nic_effective_routes
    def test_get_nic_effective_routes_success(self, mock_logger, worker):
        expected_routes = [{"route": "nic-route1"}, {"route": "nic-route2"}]
        mock_response = self._mock_response(json_data=expected_routes)

        with patch("requests.get", return_value=mock_response) as mock_get:
            result = worker.get_nic_effective_routes(
                self.SUBSCRIPTION_ID, self.RESOURCE_GROUP_NAME, self.NIC_NAME, refresh_cache=False
            )

        assert result == expected_routes
        expected_url = f"{self.DEFAULT_BASE_URL}/api/subscriptions/{self.SUBSCRIPTION_ID}/resourcegroups/{self.RESOURCE_GROUP_NAME}/networkinterfaces/{self.NIC_NAME}/routes"
        mock_get.assert_called_once_with(expected_url, params={"refresh-cache": False})
        mock_logger.debug.assert_any_call(f"Fetching effective routes for NIC {self.NIC_NAME} in resource group {self.RESOURCE_GROUP_NAME}")
        mock_logger.debug.assert_any_call(f"Fetched {len(expected_routes)} effective routes for NIC {self.NIC_NAME}")
    
    def test_get_nic_effective_routes_http_error(self, mock_logger, worker):
        error = requests.exceptions.RequestException("NIC Route Error")
        mock_response = self._mock_response(json_data={}, raise_for_status_effect=error)

        with patch("requests.get", return_value=mock_response) as mock_get:
            with pytest.raises(requests.exceptions.RequestException, match="NIC Route Error"):
                worker.get_nic_effective_routes(self.SUBSCRIPTION_ID, self.RESOURCE_GROUP_NAME, self.NIC_NAME)
        
        mock_logger.error.assert_called_once_with(f"Failed to fetch effective routes for NIC {self.NIC_NAME}: NIC Route Error")

    # Tests for execute method (dispatcher)
    def test_execute_list_route_tables(self, mock_logger, worker):
        with patch.object(worker, 'list_route_tables', return_value=[]) as mock_method:
            worker.execute(operation="list_route_tables", subscription_id=self.SUBSCRIPTION_ID, refresh_cache=True)
            mock_method.assert_called_once_with(self.SUBSCRIPTION_ID, True)

    def test_execute_get_route_table_details(self, mock_logger, worker):
        with patch.object(worker, 'get_route_table_details', return_value={}) as mock_method:
            worker.execute(
                operation="get_route_table_details", 
                subscription_id=self.SUBSCRIPTION_ID,
                resource_group_name=self.RESOURCE_GROUP_NAME,
                route_table_name=self.ROUTE_TABLE_NAME,
                refresh_cache=False
            )
            mock_method.assert_called_once_with(self.SUBSCRIPTION_ID, self.RESOURCE_GROUP_NAME, self.ROUTE_TABLE_NAME, False)

    def test_execute_get_vm_effective_routes(self, mock_logger, worker):
        with patch.object(worker, 'get_vm_effective_routes', return_value=[]) as mock_method:
            worker.execute(
                operation="get_vm_effective_routes",
                subscription_id=self.SUBSCRIPTION_ID,
                resource_group_name=self.RESOURCE_GROUP_NAME,
                vm_name=self.VM_NAME
            ) # Test default refresh_cache=False
            mock_method.assert_called_once_with(self.SUBSCRIPTION_ID, self.RESOURCE_GROUP_NAME, self.VM_NAME, False)
            
    def test_execute_get_nic_effective_routes(self, mock_logger, worker):
        with patch.object(worker, 'get_nic_effective_routes', return_value=[]) as mock_method:
            worker.execute(
                operation="get_nic_effective_routes",
                subscription_id=self.SUBSCRIPTION_ID,
                resource_group_name=self.RESOURCE_GROUP_NAME,
                nic_name=self.NIC_NAME,
                refresh_cache=True
            )
            mock_method.assert_called_once_with(self.SUBSCRIPTION_ID, self.RESOURCE_GROUP_NAME, self.NIC_NAME, True)

    def test_execute_default_operation_is_list_route_tables(self, mock_logger, worker):
        # Tests that if operation is not specified, it defaults to list_route_tables
        with patch.object(worker, 'list_route_tables', return_value=[]) as mock_method:
            worker.execute(subscription_id=self.SUBSCRIPTION_ID) # No operation kwarg
            mock_method.assert_called_once_with(self.SUBSCRIPTION_ID, False) # Default refresh_cache

    def test_execute_missing_params_list_route_tables(self, mock_logger, worker):
        with pytest.raises(ValueError, match="subscription_id is required for list_route_tables operation"):
            worker.execute(operation="list_route_tables") # Missing subscription_id

    def test_execute_missing_params_get_route_table_details(self, mock_logger, worker):
        with pytest.raises(ValueError, match="subscription_id, resource_group_name, and route_table_name are required"):
            worker.execute(operation="get_route_table_details", subscription_id=self.SUBSCRIPTION_ID)

    def test_execute_missing_params_get_vm_effective_routes(self, mock_logger, worker):
        with pytest.raises(ValueError, match="subscription_id, resource_group_name, and vm_name are required"):
            worker.execute(operation="get_vm_effective_routes", subscription_id=self.SUBSCRIPTION_ID)
            
    def test_execute_missing_params_get_nic_effective_routes(self, mock_logger, worker):
        with pytest.raises(ValueError, match="subscription_id, resource_group_name, and nic_name are required"):
            worker.execute(operation="get_nic_effective_routes", subscription_id=self.SUBSCRIPTION_ID)

    def test_execute_unsupported_operation(self, mock_logger, worker):
        with pytest.raises(ValueError, match="Unsupported operation: bogus_operation"):
            worker.execute(operation="bogus_operation")

    def test_init_custom_base_url(self, mock_logger):
        custom_url = "http://custom.host:1234"
        custom_worker = RouteTablesWorker(base_url=custom_url)
        assert custom_worker.base_url == custom_url

        # Verify it's used in a call
        expected_data = [{"name": "rt1"}]
        mock_response = self._mock_response(json_data=expected_data)
        with patch("requests.get", return_value=mock_response) as mock_get:
            custom_worker.list_route_tables(self.SUBSCRIPTION_ID)
        
        expected_url = f"{custom_url}/api/subscriptions/{self.SUBSCRIPTION_ID}/routetables"
        mock_get.assert_called_once_with(expected_url, params={"refresh-cache": False})

