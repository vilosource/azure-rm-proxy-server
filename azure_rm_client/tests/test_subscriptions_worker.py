import pytest
import requests  # Add this import
from unittest.mock import patch, MagicMock
from azure_rm_client.workers.subscriptions_worker import SubscriptionsWorker
from azure_rm_client.tests.base_worker_test import BaseWorkerTest

class TestSubscriptionsWorker(BaseWorkerTest):
    """Tests for the SubscriptionsWorker class."""

    def test_list_subscriptions_success(self):
        """Test successfully listing subscriptions."""
        # Arrange
        worker = SubscriptionsWorker(base_url="http://localhost:7890")
        expected_subscriptions = self.get_subscriptions_fixture()
        mock_response = self.create_mock_response(status_code=200, json_data=expected_subscriptions)

        # Act
        with patch("requests.get", return_value=mock_response) as mock_get:
            subscriptions = worker.list_subscriptions()

        # Assert
        assert subscriptions == expected_subscriptions
        mock_get.assert_called_once_with(
            "http://localhost:7890/api/subscriptions/",
            params={"refresh-cache": False}  # Assuming default refresh_cache is False
        )

    def test_list_subscriptions_api_error(self):
        """Test handling of API error when listing subscriptions."""
        # Arrange
        worker = SubscriptionsWorker(base_url="http://localhost:7890")
        mock_response = self.create_mock_response(status_code=500, json_data={"error": "Server Error"})

        # Act & Assert
        with patch("requests.get", return_value=mock_response) as mock_get:
            with pytest.raises(requests.exceptions.HTTPError):
                worker.list_subscriptions()
        
        mock_get.assert_called_once_with(
            "http://localhost:7890/api/subscriptions/",
            params={"refresh-cache": False}
        )

    def test_list_subscriptions_refresh_cache(self):
        """Test listing subscriptions with refresh_cache=True."""
        # Arrange
        worker = SubscriptionsWorker(base_url="http://localhost:7890")
        expected_subscriptions = self.get_subscriptions_fixture()
        mock_response = self.create_mock_response(status_code=200, json_data=expected_subscriptions)

        # Act
        with patch("requests.get", return_value=mock_response) as mock_get:
            subscriptions = worker.list_subscriptions(refresh_cache=True)

        # Assert
        assert subscriptions == expected_subscriptions
        mock_get.assert_called_once_with(
            "http://localhost:7890/api/subscriptions/",
            params={"refresh-cache": True}
        )

    def test_execute_calls_list_subscriptions(self):
        """Test that execute() calls list_subscriptions correctly."""
        # Arrange
        worker = SubscriptionsWorker(base_url="http://localhost:7890")
        expected_subscriptions = self.get_subscriptions_fixture()
        
        # Act
        with patch.object(worker, 'list_subscriptions', return_value=expected_subscriptions) as mock_list_method:
            result = worker.execute(refresh_cache=True)
        
        # Assert
        assert result == expected_subscriptions
        mock_list_method.assert_called_once_with(refresh_cache=True)

    def test_list_subscriptions_different_base_url(self):
        """Test listing subscriptions with a non-default base_url."""
        # Arrange
        custom_base_url = "http://customhost:1234"
        worker = SubscriptionsWorker(base_url=custom_base_url)
        expected_subscriptions = self.get_subscriptions_fixture()
        mock_response = self.create_mock_response(status_code=200, json_data=expected_subscriptions)

        # Act
        with patch("requests.get", return_value=mock_response) as mock_get:
            subscriptions = worker.list_subscriptions()

        # Assert
        assert subscriptions == expected_subscriptions
        mock_get.assert_called_once_with(
            f"{custom_base_url}/api/subscriptions/",
            params={"refresh-cache": False}
        )
