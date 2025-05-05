"""API endpoints for route tables and routes."""

import logging
from fastapi import Depends, APIRouter, Query, HTTPException, Path
from typing import List

from ..app.dependencies import get_azure_service
from ..core.models import RouteTableSummaryModel, RouteTableModel, RouteModel
from ..core.azure_service import AzureResourceService
from azure.core.exceptions import ResourceNotFoundError, ClientAuthenticationError

logger = logging.getLogger(__name__)

# Constants for path parameter titles
TITLE_SUBSCRIPTION_ID = "Azure Subscription ID"
TITLE_RESOURCE_GROUP = "Resource Group Name"
TITLE_ROUTE_TABLE = "Route Table Name"
TITLE_VM_NAME = "Virtual Machine Name"
TITLE_NIC_NAME = "Network Interface Name"
TITLE_AUTH_FAILED = "Authentication failed"

router = APIRouter(tags=["Route Table"], prefix="/api/subscriptions/{subscription_id}")


@router.get(
    "/routetables",
    response_model=List[RouteTableSummaryModel],
    summary="List Route Tables",
    description="Get all route tables for a subscription.",
)
async def list_route_tables(
    subscription_id: str = Path(..., title=TITLE_SUBSCRIPTION_ID),
    refresh_cache: bool = Query(False, alias="refresh-cache"),
    azure_service: AzureResourceService = Depends(get_azure_service),
):
    """
    Get all route tables for a subscription.

    Parameters:
        subscription_id: The ID of the Azure subscription
        refresh_cache: Whether to bypass cache and fetch fresh data
    """
    try:
        return await azure_service.get_route_tables(
            subscription_id, refresh_cache=refresh_cache
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ClientAuthenticationError:
        raise HTTPException(status_code=401, detail=TITLE_AUTH_FAILED)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@router.get(
    "/resourcegroups/{resource_group_name}/routetables/{route_table_name}",
    response_model=RouteTableModel,
    summary="Get Route Table Details",
    description="Get detailed information about a specific route table.",
)
async def get_route_table_details(
    subscription_id: str = Path(..., title=TITLE_SUBSCRIPTION_ID),
    resource_group_name: str = Path(..., title=TITLE_RESOURCE_GROUP),
    route_table_name: str = Path(..., title=TITLE_ROUTE_TABLE),
    refresh_cache: bool = Query(False, alias="refresh-cache"),
    azure_service: AzureResourceService = Depends(get_azure_service),
):
    """
    Get detailed information about a specific route table.

    Parameters:
        subscription_id: The ID of the Azure subscription
        resource_group_name: The name of the resource group
        route_table_name: The name of the route table
        refresh_cache: Whether to bypass cache and fetch fresh data
    """
    try:
        return await azure_service.get_route_table_details(
            subscription_id,
            resource_group_name,
            route_table_name,
            refresh_cache=refresh_cache,
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ClientAuthenticationError:
        raise HTTPException(status_code=401, detail=TITLE_AUTH_FAILED)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@router.get(
    "/resourcegroups/{resource_group_name}/virtualmachines/{vm_name}/routes",
    response_model=List[RouteModel],
    summary="Get VM Effective Routes",
    description="Get all effective routes for a specific virtual machine.",
)
async def get_vm_effective_routes(
    subscription_id: str = Path(..., title=TITLE_SUBSCRIPTION_ID),
    resource_group_name: str = Path(..., title=TITLE_RESOURCE_GROUP),
    vm_name: str = Path(..., title=TITLE_VM_NAME),
    refresh_cache: bool = Query(False, alias="refresh-cache"),
    azure_service: AzureResourceService = Depends(get_azure_service),
):
    """
    Get all effective routes for a specific virtual machine across all its network interfaces.

    Parameters:
        subscription_id: The ID of the Azure subscription
        resource_group_name: The name of the resource group
        vm_name: The name of the virtual machine
        refresh_cache: Whether to bypass cache and fetch fresh data
    """
    try:
        return await azure_service.get_vm_effective_routes(
            subscription_id, resource_group_name, vm_name, refresh_cache=refresh_cache
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ClientAuthenticationError:
        raise HTTPException(status_code=401, detail=TITLE_AUTH_FAILED)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@router.get(
    "/resourcegroups/{resource_group_name}/networkinterfaces/{nic_name}/routes",
    response_model=List[RouteModel],
    summary="Get NIC Effective Routes",
    description="Get all effective routes for a specific network interface.",
)
async def get_nic_effective_routes(
    subscription_id: str = Path(..., title=TITLE_SUBSCRIPTION_ID),
    resource_group_name: str = Path(..., title=TITLE_RESOURCE_GROUP),
    nic_name: str = Path(..., title=TITLE_NIC_NAME),
    refresh_cache: bool = Query(False, alias="refresh-cache"),
    azure_service: AzureResourceService = Depends(get_azure_service),
):
    """
    Get all effective routes for a specific network interface.

    Parameters:
        subscription_id: The ID of the Azure subscription
        resource_group_name: The name of the resource group
        nic_name: The name of the network interface
        refresh_cache: Whether to bypass cache and fetch fresh data
    """
    try:
        return await azure_service.get_nic_effective_routes(
            subscription_id, resource_group_name, nic_name, refresh_cache=refresh_cache
        )
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Network interface {nic_name} not found in resource group {resource_group_name}.",
        )
    except ClientAuthenticationError:
        raise HTTPException(status_code=401, detail=TITLE_AUTH_FAILED)
    except Exception as e:
        logger.error(
            f"Error getting effective routes for network interface {nic_name}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred getting effective routes for network interface {nic_name}.",
        )
