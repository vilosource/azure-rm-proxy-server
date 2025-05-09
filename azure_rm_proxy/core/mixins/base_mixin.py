"""Base mixin for Azure Resource Service components."""

import logging
import functools
import hashlib
import json
from typing import Any, Dict, Optional, List, Type, Callable, TypeVar, Tuple
from ..caching import CacheStrategy
from azure.core.exceptions import ResourceNotFoundError, ClientAuthenticationError
from ...app.config import settings

logger = logging.getLogger(__name__)

# Type variables for the decorator
T = TypeVar("T")
R = TypeVar("R")


def cached_azure_operation(
    model_class: Optional[Type[T]] = None, cache_key_prefix: Optional[str] = None
):
    """
    Decorator for Azure operations with caching and error handling.

    This decorator handles common patterns for Azure operations:
    1. Cache checking and retrieval
    2. Error handling
    3. Cache storage of results

    Args:
        model_class: The Pydantic model class for validation
        cache_key_prefix: Optional prefix for the cache key

    Returns:
        Decorated function
    """

    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Extract refresh_cache from kwargs
            refresh_cache = kwargs.get("refresh_cache", False)

            # Generate cache key
            func_name = func.__name__
            if cache_key_prefix:
                key_parts = [cache_key_prefix]
            else:
                key_parts = [func_name.replace("get_", "")]

            # Add function arguments to the cache key
            key_parts.extend([str(arg) for arg in args])

            # Add any important kwargs to the cache key
            for key in ["subscription_id", "resource_group_name", "name"]:
                if key in kwargs:
                    key_parts.append(str(kwargs[key]))

            cache_key = self._get_cache_key(key_parts)

            # Check cache if not refreshing
            if not refresh_cache and self.cache:
                cached_data = self.cache.get(cache_key)
                if cached_data:
                    self._log_debug(f"Cache hit for {func_name}")
                    if model_class:
                        return self._validate_cached_data(cached_data, model_class)
                    return cached_data

            # Execute the function
            try:
                self._log_info(f"Fetching data for {func_name} from Azure")
                result = await func(self, *args, **kwargs)

                # Cache the result
                if self.cache and result is not None:
                    self._set_cache_with_ttl(cache_key, result, settings.cache_ttl)
                    self._log_info(f"Cached result for {func_name}")

                return result
            except ResourceNotFoundError:
                resource_type = func_name.replace("get_", "")
                self._log_warning(f"{resource_type.capitalize()} not found")
                raise
            except ClientAuthenticationError:
                self._log_error(f"Authentication error in {func_name}")
                raise
            except Exception as e:
                self._log_error(f"Error in {func_name}: {type(e).__name__}")
                raise

        return wrapper

    return decorator


class BaseAzureResourceMixin:
    """Base mixin class with shared utility methods for Azure resource mixins."""

    def __init__(self):
        """Placeholder init method for IDE compatibility. Will not be called."""
        # This won't be called as this is a mixin, but helps with IDE autocomplete
        self.credential = None
        self.cache: Optional[CacheStrategy] = None
        self.limiter = None

    def _get_cache_key(self, key_components: list) -> str:
        """
        Create a standardized cache key from components.

        Args:
            key_components: List of strings to join for the cache key

        Returns:
            Standardized cache key
        """
        return ":".join([str(comp) for comp in key_components if comp])

    def _set_cache_with_ttl(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache with optional TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds. If None, uses the default TTL from settings.
        """
        if not self.cache:
            return

        # If TTL is provided, use set_with_ttl
        if ttl is not None:
            # Check if the cache implementation has a set_with_ttl method
            if hasattr(self.cache, "set_with_ttl"):
                self.cache.set_with_ttl(key, value, ttl)
            else:
                # Fallback to regular set if set_with_ttl is not available
                self.cache.set(key, value)
        else:
            # No TTL provided, use regular set
            self.cache.set(key, value)

    def _log_debug(self, message: str) -> None:
        """
        Log a debug message.

        Args:
            message: Message to log
        """
        logger.debug(message)

    def _log_info(self, message: str) -> None:
        """
        Log an info message.

        Args:
            message: Message to log
        """
        logger.info(message)

    def _log_warning(self, message: str) -> None:
        """
        Log a warning message.

        Args:
            message: Message to log
        """
        logger.warning(message)

    def _log_error(self, message: str) -> None:
        """
        Log an error message.

        Args:
            message: Message to log
        """
        logger.error(message)

    def _validate_cached_data(self, data: Any, model_class):
        """
        Ensure cached data conforms to the expected model class.

        When data is retrieved from the cache (especially Redis), Pydantic models
        are returned as dictionaries. This helper method ensures the data is
        converted back to the appropriate Pydantic model type.

        Args:
            data: The data retrieved from cache
            model_class: The Pydantic model class to validate against

        Returns:
            Data converted to the appropriate model class if needed
        """
        if data is None:
            return None

        # Handle list of items
        if isinstance(data, list):
            # If empty list, just return it
            if not data:
                return data

            # If list contains dictionaries, convert each to the model
            if isinstance(data[0], dict):
                return [model_class.model_validate(item) for item in data]

            # Otherwise, assume the list already contains model instances
            return data

        # Handle single dictionary
        if isinstance(data, dict):
            return model_class.model_validate(data)

        # Already a model instance or other type
        return data

    def _extract_resource_group_from_id(
        self, resource_id: str, default_rg: Optional[str] = None
    ) -> Optional[str]:
        """
        Extract resource group name from an Azure resource ID.

        Args:
            resource_id: Azure resource ID
            default_rg: Default resource group to return if extraction fails

        Returns:
            Resource group name or None if extraction fails and no default is provided
        """
        parts = resource_id.split("/")
        if len(parts) >= 5 and parts[3].lower() == "resourcegroups":
            return parts[4]
        return default_rg

    async def _get_client(self, client_type: str, subscription_id: str):
        """
        Get an Azure client of the specified type with concurrency control.

        Args:
            client_type: Type of client to create ('compute', 'network', 'resource', etc.)
            subscription_id: Azure subscription ID

        Returns:
            Azure client instance
        """
        from ..azure_clients import AzureClientFactory

        async with self.limiter:
            client = None
            if client_type == "compute":
                client = AzureClientFactory.create_compute_client(subscription_id, self.credential)
            elif client_type == "network":
                client = AzureClientFactory.create_network_client(subscription_id, self.credential)
            elif client_type == "resource":
                client = AzureClientFactory.create_resource_client(subscription_id, self.credential)
            elif client_type == "subscription":
                client = AzureClientFactory.create_subscription_client(self.credential)
            elif client_type == "authorization":
                client = AzureClientFactory.create_authorization_client(
                    subscription_id, self.credential
                )
            else:
                raise ValueError(f"Unsupported client type: {client_type}")

            # Add response logging policy if enabled
            if settings.log_level == "DEBUG" and hasattr(client, "_config"):
                self._add_response_logging_policy(client)

            return client

    def _add_response_logging_policy(self, client):
        """
        Add a policy to log API responses.

        Args:
            client: Azure client to add logging policy to
        """
        from azure.core.pipeline.policies import SansIOHTTPPolicy

        # Create custom policy to log responses
        class ResponseLoggingPolicy(SansIOHTTPPolicy):
            def __init__(self, logger):
                self.logger = logger

            def on_response(self, request, response):
                try:
                    # Only log on successful responses
                    if response.http_response.status_code < 400:
                        service = (
                            request.http_request.url.split("/")[4]
                            if len(request.http_request.url.split("/")) > 4
                            else "unknown"
                        )
                        operation = (
                            request.http_request.url.split("/")[-2]
                            if len(request.http_request.url.split("/")) > 2
                            else "unknown"
                        )

                        # Try to parse response as JSON
                        response_text = response.http_response.text()
                        try:
                            response_json = json.loads(response_text)
                            # Truncate response if it's too large
                            if len(response_text) > 5000:
                                truncated_json = {
                                    "value": (
                                        response_json.get("value", [])[:3]
                                        if isinstance(response_json.get("value"), list)
                                        else response_json.get("value")
                                    ),
                                    "truncated": True,
                                    "total_size": len(response_text),
                                }
                                response_text = json.dumps(truncated_json)
                            else:
                                response_text = json.dumps(response_json)
                        except:
                            # If not JSON or parsing fails, truncate the text
                            if len(response_text) > 1000:
                                response_text = response_text[:1000] + "... [truncated]"

                        self.logger.debug(
                            f"Azure API Response: {service}/{operation} - "
                            f"Status: {response.http_response.status_code} - "
                            f"Response Body: {response_text}"
                        )
                except Exception as e:
                    self.logger.debug(f"Error logging response: {str(e)}")

        # Create specialized logger for API responses
        api_logger = logging.getLogger("azure_rm_proxy.azure_api.responses")

        # Add policy to client
        if hasattr(client, "_config") and hasattr(client._config, "http_logging_policy"):
            client._config.custom_hook_policy = ResponseLoggingPolicy(api_logger)

    def _convert_to_model(self, azure_obj, model_class, **extra_fields):
        """
        Convert an Azure SDK object to a Pydantic model.

        Args:
            azure_obj: Azure SDK object
            model_class: Pydantic model class to convert to
            **extra_fields: Additional fields to include in the model

        Returns:
            Instance of model_class
        """
        # Create a dictionary of fields from the Azure object's attributes
        obj_dict = {}

        # Get field names from the model class
        model_fields = model_class.__annotations__.keys()

        # Try to map common fields
        for field in model_fields:
            # Convert field_name to attribute_name (e.g., resource_group to resourceGroup)
            snake_to_camel = "".join(
                word.capitalize() if i > 0 else word for i, word in enumerate(field.split("_"))
            )

            # Check various attribute naming patterns
            if hasattr(azure_obj, field):
                obj_dict[field] = getattr(azure_obj, field)
            elif hasattr(azure_obj, snake_to_camel):
                obj_dict[field] = getattr(azure_obj, snake_to_camel)
            elif field == "id" and hasattr(azure_obj, "id"):
                obj_dict[field] = azure_obj.id

        # Add any extra fields
        obj_dict.update(extra_fields)

        # Validate and create the model
        return model_class.model_validate(obj_dict)

    def _generate_peering_pair_id(self, vnet1_id: str, vnet2_id: str) -> str:
        """
        Generate a consistent ID for a peering pair regardless of the order.

        Args:
            vnet1_id: First VNet ID
            vnet2_id: Second VNet ID

        Returns:
            A consistent ID for the peering pair
        """
        # Sort to ensure consistency
        vnet_ids = sorted([vnet1_id, vnet2_id])
        # Create a hash of the two IDs to use as a unique identifier
        combined = f"{vnet_ids[0]}:{vnet_ids[1]}"
        return hashlib.md5(combined.encode()).hexdigest()

    async def _get_vnet_info_from_id(
        self, vnet_id: str, refresh_cache: bool = False
    ) -> Optional[Tuple[str, str, str]]:
        """
        Extract subscription ID, resource group, and VNet name from a VNet ID.

        Args:
            vnet_id: The full Azure resource ID of the virtual network
            refresh_cache: Whether to refresh the cache

        Returns:
            Tuple of (subscription_id, resource_group, vnet_name) or None if parsing fails
        """
        try:
            # Azure resource IDs follow this pattern:
            # /subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{vnet_name}
            parts = vnet_id.split("/")
            if len(parts) >= 9 and parts[1] == "subscriptions" and parts[3] == "resourceGroups":
                subscription_id = parts[2]
                resource_group = parts[4]
                vnet_name = parts[8]
                return (subscription_id, resource_group, vnet_name)
            else:
                self._log_warning(f"Could not parse VNet ID: {vnet_id}")
                return None
        except Exception as e:
            self._log_error(f"Error parsing VNet ID {vnet_id}: {str(e)}")
            return None
