from azure.identity import DefaultAzureCredential
import logging

logger = logging.getLogger(__name__)


def get_credentials():
    """Obtain Azure credentials via DefaultAzureCredential (env vars or CLI)."""
    try:
        credential = DefaultAzureCredential()
        # Attempt to get a token to verify credentials
        credential.get_token("https://management.azure.com/.default")
        logger.info("Azure credentials obtained successfully.")
        return credential
    except Exception as e:
        logger.error(f"Failed to obtain Azure credentials: {e}")
        raise
