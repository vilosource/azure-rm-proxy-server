"""AAD group functionality mixin for Azure Resource Service."""

import logging
from typing import List

from azure.core.exceptions import ClientAuthenticationError

from ..models import AADGroupModel
from .base_mixin import BaseAzureResourceMixin

logger = logging.getLogger(__name__)


class AADGroupMixin(BaseAzureResourceMixin):
    """Mixin for Azure AD group-related operations."""

    async def _fetch_aad_groups(self, subscription_id, vm):
        """
        Fetch AAD groups that have access to the VM with proper display names.

        Args:
            subscription_id: Subscription ID
            vm: Azure VM object

        Returns:
            List of AADGroupModel objects
        """
        aad_groups = []

        try:
            # Get authorization client with the new helper method
            authorization_client = await self._get_client(
                "authorization", subscription_id
            )
            role_assignments = []

            self._log_debug(f"Fetching role assignments for VM: {vm.id}")
            for ra in authorization_client.role_assignments.list_for_scope(scope=vm.id):
                if (
                    hasattr(ra, "principal_type")
                    and ra.principal_type == "Group"
                    and hasattr(ra, "principal_id")
                ):
                    role_assignments.append(ra)

            self._log_debug(f"Found {len(role_assignments)} group role assignments")

            # First, try to get the role definitions for better naming
            for ra in role_assignments:
                group_id = ra.principal_id
                try:
                    # Get role definition for better naming
                    if hasattr(ra, "role_definition_id") and ra.role_definition_id:
                        role_def_id = ra.role_definition_id
                        try:
                            # Extract the info needed to get role definition
                            # Role definition IDs are in format: /subscriptions/{subId}/providers/Microsoft.Authorization/roleDefinitions/{roleDefId}
                            parts = role_def_id.split("/")
                            if len(parts) >= 6:
                                # Get the role definition with more specific details
                                role_def = (
                                    authorization_client.role_definitions.get_by_id(
                                        role_def_id
                                    )
                                )
                                role_name = (
                                    role_def.role_name
                                    if hasattr(role_def, "role_name")
                                    else "Unknown Role"
                                )

                                # Use our helper method to create the AADGroupModel
                                display_name = f"{role_name} Group ({group_id})"
                                aad_groups.append(
                                    self._convert_to_model(
                                        {"id": group_id, "display_name": display_name},
                                        AADGroupModel,
                                    )
                                )
                                continue
                        except Exception as role_error:
                            self._log_warning(
                                f"Error getting role definition for {role_def_id}: {str(role_error)}"
                            )
                except Exception as e:
                    self._log_warning(f"Error processing role assignment: {str(e)}")

                # If we get here, we couldn't get role info, so add the basic format
                if not any(g.id == group_id for g in aad_groups):
                    aad_groups.append(
                        self._convert_to_model(
                            {"id": group_id, "display_name": f"Group {group_id}"},
                            AADGroupModel,
                        )
                    )

            # If we have the Microsoft Graph SDK, try to enhance the names further
            try:
                # Import here to avoid issues if not installed
                from azure.identity import DefaultAzureCredential
                from msgraph.core import GraphClient

                graph_client = GraphClient(credential=DefaultAzureCredential())

                # Try to update the display names with Graph API
                updated_groups = []
                for group in aad_groups:
                    try:
                        # Try to get group details from Microsoft Graph
                        response = graph_client.get(f"/groups/{group.id}")
                        if response.status_code == 200:
                            group_data = response.json()
                            display_name = group_data.get(
                                "displayName", group.display_name
                            )
                            description = group_data.get("description", "")

                            if description:
                                full_name = f"{display_name} - {description}"
                            else:
                                full_name = display_name

                            updated_groups.append(
                                self._convert_to_model(
                                    {"id": group.id, "display_name": full_name},
                                    AADGroupModel,
                                )
                            )
                            self._log_debug(
                                f"Enhanced group name with Graph API: {full_name}"
                            )
                        else:
                            updated_groups.append(group)
                    except Exception as graph_error:
                        self._log_warning(
                            f"Could not fetch group details from Graph API for {group.id}: {str(graph_error)}"
                        )
                        updated_groups.append(group)

                if updated_groups:
                    aad_groups = updated_groups

            except ImportError:
                self._log_warning(
                    "Microsoft Graph SDK not available, using role-based group information"
                )
            except Exception as e:
                self._log_warning(f"Error using Microsoft Graph client: {str(e)}")

        except ClientAuthenticationError as e:
            self._log_warning(
                f"Authentication error fetching role assignments: {str(e)}"
            )
        except Exception as e:
            self._log_warning(f"Could not fetch role assignments: {str(e)}")

        self._log_debug(f"Fetched {len(aad_groups)} AAD group assignments")
        return aad_groups
