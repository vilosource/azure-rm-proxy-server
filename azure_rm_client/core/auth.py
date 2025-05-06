from azure.identity import DefaultAzureCredential
import logging

logger = logging.getLogger(__name__)

class AzureAuth:
    """
    Authentication handler for Azure services.
    Uses DefaultAzureCredential to handle authentication to Azure.
    """
    
    async def get_credentials(self):
        """
        Get Azure credentials using DefaultAzureCredential.
        
        Returns:
            DefaultAzureCredential: Azure credential object.
        """
        try:
            logger.info("Getting Azure credentials")
            credential = DefaultAzureCredential()
            # Verify credentials work by requesting a token
            credential.get_token("https://management.azure.com/.default")
            logger.info("Azure credentials obtained successfully")
            return credential
        except Exception as e:
            logger.error(f"Failed to obtain Azure credentials: {e}")
            raise