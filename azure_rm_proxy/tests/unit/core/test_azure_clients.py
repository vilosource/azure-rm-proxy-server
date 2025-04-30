import pytest
from unittest.mock import patch, MagicMock
from azure_rm_proxy.core.azure_clients import AzureClientFactory


class TestAzureClientFactory:
    """Test suite for Azure client factory functionality."""

    @patch("azure_rm_proxy.core.azure_clients.SubscriptionClient")
    def test_create_subscription_client(self, mock_subscription_client):
        """Test creation of SubscriptionClient."""
        # Arrange
        mock_credential = MagicMock()
        mock_instance = MagicMock()
        mock_subscription_client.return_value = mock_instance

        # Act
        result = AzureClientFactory.create_subscription_client(mock_credential)

        # Assert
        assert result == mock_instance
        mock_subscription_client.assert_called_once_with(mock_credential)

    @patch("azure_rm_proxy.core.azure_clients.ResourceManagementClient")
    def test_create_resource_client(self, mock_resource_client):
        """Test creation of ResourceManagementClient."""
        # Arrange
        mock_credential = MagicMock()
        subscription_id = "test-subscription-id"
        mock_instance = MagicMock()
        mock_resource_client.return_value = mock_instance

        # Act
        result = AzureClientFactory.create_resource_client(
            subscription_id, mock_credential
        )

        # Assert
        assert result == mock_instance
        mock_resource_client.assert_called_once_with(mock_credential, subscription_id)

    @patch("azure_rm_proxy.core.azure_clients.ComputeManagementClient")
    def test_create_compute_client(self, mock_compute_client):
        """Test creation of ComputeManagementClient."""
        # Arrange
        mock_credential = MagicMock()
        subscription_id = "test-subscription-id"
        mock_instance = MagicMock()
        mock_compute_client.return_value = mock_instance

        # Act
        result = AzureClientFactory.create_compute_client(
            subscription_id, mock_credential
        )

        # Assert
        assert result == mock_instance
        mock_compute_client.assert_called_once_with(mock_credential, subscription_id)

    @patch("azure_rm_proxy.core.azure_clients.NetworkManagementClient")
    def test_create_network_client(self, mock_network_client):
        """Test creation of NetworkManagementClient."""
        # Arrange
        mock_credential = MagicMock()
        subscription_id = "test-subscription-id"
        mock_instance = MagicMock()
        mock_network_client.return_value = mock_instance

        # Act
        result = AzureClientFactory.create_network_client(
            subscription_id, mock_credential
        )

        # Assert
        assert result == mock_instance
        mock_network_client.assert_called_once_with(mock_credential, subscription_id)

    @patch("azure_rm_proxy.core.azure_clients.AuthorizationManagementClient")
    def test_create_authorization_client(self, mock_auth_client):
        """Test creation of AuthorizationManagementClient."""
        # Arrange
        mock_credential = MagicMock()
        subscription_id = "test-subscription-id"
        mock_instance = MagicMock()
        mock_auth_client.return_value = mock_instance

        # Act
        result = AzureClientFactory.create_authorization_client(
            subscription_id, mock_credential
        )

        # Assert
        assert result == mock_instance
        mock_auth_client.assert_called_once_with(mock_credential, subscription_id)
