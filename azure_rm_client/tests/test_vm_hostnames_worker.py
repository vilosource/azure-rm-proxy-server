import pytest
from unittest.mock import patch, MagicMock, mock_open
import requests # For requests.exceptions
import os
import json

from azure_rm_client.workers.vm_hostnames_worker import VMHostnamesWorker

# Patch logging.getLogger globally
@patch('logging.getLogger')
class TestVMHostnamesWorker:
    """Tests for the VMHostnamesWorker class."""

    SUBSCRIPTION_ID = "test-sub-id"
    DEFAULT_BASE_URL = "http://localhost:8000" # As hardcoded in the worker's method

    @pytest.fixture
    def worker(self):
        """Fixture to create a VMHostnamesWorker instance."""
        return VMHostnamesWorker() # __init__ takes no args

    def _mock_response(self, json_data, status_code=200, raise_for_status_effect=None):
        mock_resp = MagicMock()
        mock_resp.status_code = status_code
        mock_resp.json.return_value = json_data
        if raise_for_status_effect:
            mock_resp.raise_for_status.side_effect = raise_for_status_effect
        else:
            mock_resp.raise_for_status = MagicMock()
        return mock_resp

    # Tests for list_vm_hostnames
    def test_list_vm_hostnames_success_no_sub(self, mock_get_logger, worker):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        expected_hostnames = [{"vm_name": "vm1", "hostname": "host1"}]
        mock_response = self._mock_response(json_data=expected_hostnames)
        
        with patch("requests.get", return_value=mock_response) as mock_get:
            result = worker.list_vm_hostnames(refresh_cache=False)

        assert result == expected_hostnames
        expected_url = f"{self.DEFAULT_BASE_URL}/api/subscriptions/hostnames/"
        mock_get.assert_called_once_with(expected_url, params={"subscription-id": None, "refresh-cache": False})
        mock_logger.debug.assert_any_call(
            f"Fetching VM hostnames with subscription_id={None} and refresh_cache={False}"
        )
        mock_logger.debug.assert_any_call(f"Fetched VM hostnames: {expected_hostnames}")

    def test_list_vm_hostnames_success_with_sub_and_refresh(self, mock_get_logger, worker):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        expected_hostnames = [{"vm_name": "vm2", "hostname": "host2"}]
        mock_response = self._mock_response(json_data=expected_hostnames)

        with patch("requests.get", return_value=mock_response) as mock_get:
            result = worker.list_vm_hostnames(subscription_id=self.SUBSCRIPTION_ID, refresh_cache=True)

        assert result == expected_hostnames
        expected_url = f"{self.DEFAULT_BASE_URL}/api/subscriptions/hostnames/"
        mock_get.assert_called_once_with(expected_url, params={"subscription-id": self.SUBSCRIPTION_ID, "refresh-cache": True})
        mock_logger.debug.assert_any_call(
            f"Fetching VM hostnames with subscription_id={self.SUBSCRIPTION_ID} and refresh_cache={True}"
        )

    def test_list_vm_hostnames_api_error(self, mock_get_logger, worker):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        error = requests.exceptions.RequestException("API Network Error")
        # Patch requests.get to raise the exception directly
        with patch("requests.get", side_effect=error) as mock_get:
            with pytest.raises(requests.exceptions.RequestException, match="API Network Error"):
                worker.list_vm_hostnames()
        
        mock_logger.error.assert_called_once_with(f"Failed to fetch VM hostnames: API Network Error")

    # Tests for execute
    def test_execute_success(self, mock_get_logger, worker):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        output_dir = "/fake/output_dir"
        expected_hostnames_data = [{"vm_name": "vm_exec", "hostname": "host_exec"}]

        with patch.object(worker, 'list_vm_hostnames', return_value=expected_hostnames_data) as mock_list_method:
            with patch("builtins.open", mock_open()) as mocked_file_open:
                with patch("json.dump") as mock_json_dump:
                    worker.execute(output_dir=output_dir, subscription_id=self.SUBSCRIPTION_ID, refresh_cache=True)

        mock_list_method.assert_called_once_with(subscription_id=self.SUBSCRIPTION_ID, refresh_cache=True)

        expected_file_path = os.path.join(output_dir, "vm-name_hostname_list.json")
        mocked_file_open.assert_called_once_with(expected_file_path, "w")
        mock_json_dump.assert_called_once_with(expected_hostnames_data, mocked_file_open.return_value, indent=2)

        mock_logger.debug.assert_called_once_with(f"VM hostnames saved to {expected_file_path}")

    def test_execute_list_vm_hostnames_failure(self, mock_get_logger, worker):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        output_dir = "/another/fake_dir"
        
        with patch.object(worker, 'list_vm_hostnames', side_effect=requests.exceptions.RequestException("List Error")) as mock_list_method:
            with pytest.raises(requests.exceptions.RequestException, match="List Error"):
                worker.execute(output_dir=output_dir)
        
        mock_list_method.assert_called_once_with(subscription_id=None, refresh_cache=False)
        # list_vm_hostnames would log its own error, which is tested in test_list_vm_hostnames_api_error

    def test_execute_file_write_error(self, mock_get_logger, worker):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        output_dir = "/yet_another/dir"
        hostnames_data = [{"vm": "test"}]

        with patch.object(worker, 'list_vm_hostnames', return_value=hostnames_data):
            with patch("builtins.open", mock_open()) as mocked_file_open:
                mocked_file_open.side_effect = IOError("Cannot write")
                with pytest.raises(IOError, match="Cannot write"):
                    worker.execute(output_dir=output_dir)
        
        expected_file_path = os.path.join(output_dir, "vm-name_hostname_list.json")
        mocked_file_open.assert_called_once_with(expected_file_path, "w")
        # json.dump would not be called in this scenario
        # The logger call from execute about saving would also not be reached.
