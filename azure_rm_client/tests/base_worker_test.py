import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Dict, List, Any, Optional, Union  # Add Union
import requests  # Add requests for exception handling in mock

class BaseWorkerTest:
    """Base class for all worker tests using fixture data."""

    @staticmethod
    def get_fixture_path() -> Path:
        """Get the path to the test fixtures directory."""
        # Assumes tests are run from the root of the azure-rm-proxy-server directory
        # or that this file is in azure_rm_client/tests/
        return Path(__file__).parent / "fixtures"

    def load_json_fixture(self, file_path: Union[str, Path]) -> Any:
        """Load a JSON file from the fixtures directory."""
        full_path = self.get_fixture_path() / file_path
        try:
            with open(full_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            pytest.fail(f"Failed to load test fixture from {full_path}: {e}")

    def get_subscriptions_fixture(self) -> List[Dict[str, Any]]:
        """Get subscriptions data from fixtures."""
        return self.load_json_fixture("subscriptions.json")

    def get_resource_groups_fixture(self, subscription_id: str) -> List[Dict[str, Any]]:
        """Get resource groups for a specific subscription from fixtures."""
        return self.load_json_fixture(f"resource_groups/{subscription_id}/resource_groups.json")

    def get_resource_group_details_fixture(self, subscription_id: str, rg_name: str) -> Dict[str, Any]:
        """Get resource group details for a specific resource group from fixtures."""
        return self.load_json_fixture(f"resource_groups/{subscription_id}/{rg_name}.json")

    def get_virtual_machines_fixture(self, subscription_id: str, resource_group_name: str) -> List[Dict[str, Any]]:
        """Get virtual machines for a specific resource group from fixtures."""
        vm_list = []
        vm_dir = self.get_fixture_path() / "virtual_machines" / subscription_id / resource_group_name
        if vm_dir.exists() and vm_dir.is_dir():
            for vm_file in vm_dir.glob("*.json"):
                vm_list.append(self.load_json_fixture(vm_file.relative_to(self.get_fixture_path())))
        return vm_list
        
    def get_virtual_machine_details_fixture(self, subscription_id: str, resource_group_name: str, vm_name: str) -> Dict[str, Any]:
        """Get virtual machine details for a specific VM from fixtures."""
        return self.load_json_fixture(f"virtual_machines/{subscription_id}/{resource_group_name}/{vm_name}.json")

    def get_route_tables_fixture(self, subscription_id: str) -> List[Dict[str, Any]]:
        """Get route tables for a specific subscription from fixtures."""
        return self.load_json_fixture(f"route_tables/{subscription_id}/route_tables.json")

    def get_route_table_details_fixture(self, subscription_id: str, rt_name: str) -> Dict[str, Any]:
        """Get route table details for a specific route table from fixtures."""
        return self.load_json_fixture(f"route_tables/{subscription_id}/{rt_name}.json")
        
    def get_vm_report_fixture(self) -> List[Dict[str, Any]]:
        """Get VM report data from fixtures."""
        return self.load_json_fixture("reports/virtual-machine-report.json")

    @staticmethod
    def create_mock_response(status_code: int = 200, json_data: Optional[Any] = None, text_data: Optional[str] = None, headers: Optional[Dict[str, str]] = None) -> MagicMock:
        """Create a mock requests.Response object."""
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.json.return_value = json_data
        mock_response.text = text_data if text_data is not None else json.dumps(json_data) if json_data is not None else ""
        mock_response.headers = headers or {"Content-Type": "application/json"}
        
        if status_code >= 400:
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        else:
            mock_response.raise_for_status = MagicMock()
            
        return mock_response