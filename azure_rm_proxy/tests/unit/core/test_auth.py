import pytest
from unittest.mock import patch, MagicMock
import logging
from azure_rm_proxy.core.auth import get_credentials

# Set up logging for tests
logging.basicConfig(level=logging.INFO)


class TestAuth:
    """Test suite for authentication functionality."""

    @patch("azure_rm_proxy.core.auth.DefaultAzureCredential")
    def test_get_credentials_success(self, mock_default_credential):
        """Test successful credential acquisition."""
        # Arrange
        mock_credential = MagicMock()
        mock_default_credential.return_value = mock_credential

        # Act
        result = get_credentials()

        # Assert
        assert result == mock_credential
        mock_credential.get_token.assert_called_once_with(
            "https://management.azure.com/.default"
        )

    @patch("azure_rm_proxy.core.auth.DefaultAzureCredential")
    def test_get_credentials_failure(self, mock_default_credential):
        """Test credential acquisition failure."""
        # Arrange
        mock_credential = MagicMock()
        mock_default_credential.return_value = mock_credential
        mock_credential.get_token.side_effect = Exception("Authentication failed")

        # Act & Assert
        with pytest.raises(Exception) as excinfo:
            get_credentials()

        assert "Authentication failed" in str(excinfo.value)
        mock_credential.get_token.assert_called_once_with(
            "https://management.azure.com/.default"
        )
