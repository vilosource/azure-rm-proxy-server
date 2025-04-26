from azure.mgmt.resource import SubscriptionClient, ResourceManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.authorization import AuthorizationManagementClient
import logging

logger = logging.getLogger(__name__)


class AzureClientFactory:
    """Factory for creating Azure SDK clients."""

    @staticmethod
    def create_subscription_client(credential):
        logger.debug("Creating SubscriptionClient")
        return SubscriptionClient(credential)

    @staticmethod
    def create_resource_client(subscription_id, credential):
        logger.debug(
            f"Creating ResourceManagementClient for subscription {subscription_id}"
        )
        return ResourceManagementClient(credential, subscription_id)

    @staticmethod
    def create_compute_client(subscription_id, credential):
        logger.debug(
            f"Creating ComputeManagementClient for subscription {subscription_id}"
        )
        return ComputeManagementClient(credential, subscription_id)

    @staticmethod
    def create_network_client(subscription_id, credential):
        logger.debug(
            f"Creating NetworkManagementClient for subscription {subscription_id}"
        )
        return NetworkManagementClient(credential, subscription_id)

    @staticmethod
    def create_authorization_client(subscription_id, credential):
        logger.debug(
            f"Creating AuthorizationManagementClient for subscription {subscription_id}"
        )
        return AuthorizationManagementClient(credential, subscription_id)
