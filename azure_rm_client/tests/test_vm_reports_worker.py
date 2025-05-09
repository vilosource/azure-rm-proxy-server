import pytest
from unittest.mock import patch, MagicMock
import requests # For requests.exceptions

from azure_rm_client.workers.vm_reports_worker import VMReportsWorker

# Patch the module-level logger used by the worker
@patch('azure_rm_client.workers.vm_reports_worker.logging', new_callable=MagicMock)
class TestVMReportsWorker:
    """Tests for the VMReportsWorker class."""

    DEFAULT_BASE_URL = "http://localhost:8000"

    @pytest.fixture
    def worker(self):
        """Fixture to create a VMReportsWorker instance."""
        return VMReportsWorker(base_url=self.DEFAULT_BASE_URL)

    def _mock_response(self, json_data, status_code=200, raise_for_status_effect=None):
        mock_resp = MagicMock()
        mock_resp.status_code = status_code
        mock_resp.json.return_value = json_data
        if raise_for_status_effect:
            mock_resp.raise_for_status.side_effect = raise_for_status_effect
        else:
            mock_resp.raise_for_status = MagicMock()
        return mock_resp

    # Tests for generate_vm_report
    def test_generate_vm_report_success(self, mock_logging, worker):
        mock_logger_instance = mock_logging.getLogger.return_value
        expected_report = [{"vm_id": "vm1", "status": "running"}, {"vm_id": "vm2", "status": "stopped"}]
        mock_response = self._mock_response(json_data=expected_report)
        
        with patch("requests.get", return_value=mock_response) as mock_get:
            result = worker.generate_vm_report(refresh_cache=False)

        assert result == expected_report
        expected_url = f"{self.DEFAULT_BASE_URL}/api/reports/virtual-machines"
        mock_get.assert_called_once_with(expected_url, params={"refresh-cache": False})
        mock_logger_instance.debug.assert_any_call(f"Fetching VM report with refresh_cache={False}")
        mock_logger_instance.debug.assert_any_call("Fetched VM report")

    def test_generate_vm_report_with_refresh_cache(self, mock_logging, worker):
        mock_logger_instance = mock_logging.getLogger.return_value
        expected_report = [{"vm_id": "vm_fresh", "status": "running"}]
        mock_response = self._mock_response(json_data=expected_report)

        with patch("requests.get", return_value=mock_response) as mock_get:
            result = worker.generate_vm_report(refresh_cache=True)

        assert result == expected_report
        expected_url = f"{self.DEFAULT_BASE_URL}/api/reports/virtual-machines"
        mock_get.assert_called_once_with(expected_url, params={"refresh-cache": True})
        mock_logger_instance.debug.assert_any_call(f"Fetching VM report with refresh_cache={True}")

    def test_generate_vm_report_api_error(self, mock_logging, worker):
        mock_logger_instance = mock_logging.getLogger.return_value
        error = requests.exceptions.HTTPError("Report API Error")
        mock_response = self._mock_response(json_data={}, raise_for_status_effect=error)
        
        with patch("requests.get", return_value=mock_response) as mock_get:
            with pytest.raises(requests.exceptions.HTTPError, match="Report API Error"):
                worker.generate_vm_report()
        
        mock_logger_instance.error.assert_called_once_with(f"Failed to fetch VM report: Report API Error")

    # Tests for execute method
    def test_execute_calls_generate_vm_report(self, mock_logging, worker):
        mock_logger_instance = mock_logging.getLogger.return_value # For logger in generate_vm_report
        expected_report_data = [{"report_item": "data"}]

        with patch.object(worker, 'generate_vm_report', return_value=expected_report_data) as mock_generate_method:
            result = worker.execute(refresh_cache=True)
        
        assert result == expected_report_data
        mock_generate_method.assert_called_once_with(refresh_cache=True)

    def test_execute_default_refresh_cache_is_false(self, mock_logging, worker):
        mock_logger_instance = mock_logging.getLogger.return_value
        with patch.object(worker, 'generate_vm_report', return_value=[]) as mock_generate_method:
            worker.execute() # No kwargs
        
        mock_generate_method.assert_called_once_with(refresh_cache=False)

    def test_execute_passes_kwargs_to_generate_vm_report(self, mock_logging, worker):
        mock_logger_instance = mock_logging.getLogger.return_value
        with patch.object(worker, 'generate_vm_report', return_value=[]) as mock_generate_method:
            worker.execute(refresh_cache=True, other_arg="test") # other_arg is not used by execute but good to test it passes kwargs
        
        # The execute method specifically extracts refresh_cache, other args are not passed to generate_vm_report
        mock_generate_method.assert_called_once_with(refresh_cache=True)

    def test_init_custom_base_url(self, mock_logging):
        """Test worker initialization with a custom base URL."""
        mock_logger_instance = mock_logging.getLogger.return_value
        custom_url = "http://custom.report.host:9999"
        custom_worker = VMReportsWorker(base_url=custom_url)
        assert custom_worker.base_url == custom_url

        # Verify the custom URL is used in a call via execute
        expected_data = [{"report": "custom_url_report"}]
        mock_response = self._mock_response(json_data=expected_data)
        with patch("requests.get", return_value=mock_response) as mock_get:
            custom_worker.execute()
        
        expected_url_call = f"{custom_url}/api/reports/virtual-machines"
        mock_get.assert_called_once_with(expected_url_call, params={"refresh-cache": False})

