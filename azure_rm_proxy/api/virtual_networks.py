"""API endpoints for virtual networks."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from starlette.status import HTTP_404_NOT_FOUND

from ..app.dependencies import get_azure_service
from ..core.models import VirtualNetworkModel
from ..core.azure_service import AzureResourceService

router = APIRouter(tags=["Virtual Networks"], prefix="/api/virtual-networks")


@router.get(
    "/subscriptions/{subscription_id}",
    response_model=List[VirtualNetworkModel],
    summary="List virtual networks in a subscription",
    description="Returns a list of all virtual networks in the specified subscription.",
)
async def list_virtual_networks(
    subscription_id: str,
    resource_group: Optional[str] = Query(None, description="Filter by resource group"),
    refresh_cache: bool = Query(
        False, alias="refresh-cache", description="Whether to bypass cache and fetch fresh data"
    ),
    azure_service: AzureResourceService = Depends(get_azure_service),
) -> List[VirtualNetworkModel]:
    """
    List virtual networks in a subscription.

    Args:
        subscription_id: Azure subscription ID
        resource_group: Optional resource group name to filter by
        refresh_cache: Whether to bypass cache and fetch fresh data
        azure_service: Azure resource service

    Returns:
        List of virtual networks
    """
    return await azure_service.list_virtual_networks(
        subscription_id=subscription_id,
        resource_group_name=resource_group,
        refresh_cache=refresh_cache,
    )


@router.get(
    "/subscriptions/{subscription_id}/resource-groups/{resource_group}",
    response_model=List[VirtualNetworkModel],
    summary="List virtual networks in a resource group",
    description="Returns a list of all virtual networks in the specified resource group.",
)
async def list_resource_group_virtual_networks(
    subscription_id: str,
    resource_group: str,
    refresh_cache: bool = Query(
        False, alias="refresh-cache", description="Whether to bypass cache and fetch fresh data"
    ),
    azure_service: AzureResourceService = Depends(get_azure_service),
) -> List[VirtualNetworkModel]:
    """
    List virtual networks in a resource group.

    Args:
        subscription_id: Azure subscription ID
        resource_group: Resource group name
        refresh_cache: Whether to bypass cache and fetch fresh data
        azure_service: Azure resource service

    Returns:
        List of virtual networks in the resource group
    """
    return await azure_service.list_virtual_networks(
        subscription_id=subscription_id,
        resource_group_name=resource_group,
        refresh_cache=refresh_cache,
    )


@router.get(
    "/subscriptions/{subscription_id}/resource-groups/{resource_group}/{vnet_name}",
    response_model=VirtualNetworkModel,
    summary="Get virtual network details",
    description="Returns detailed information about a specific virtual network.",
)
async def get_virtual_network(
    subscription_id: str,
    resource_group: str,
    vnet_name: str,
    refresh_cache: bool = Query(
        False, alias="refresh-cache", description="Whether to bypass cache and fetch fresh data"
    ),
    azure_service: AzureResourceService = Depends(get_azure_service),
) -> VirtualNetworkModel:
    """
    Get details of a specific virtual network.

    Args:
        subscription_id: Azure subscription ID
        resource_group: Resource group name
        vnet_name: Virtual network name
        refresh_cache: Whether to bypass cache and fetch fresh data
        azure_service: Azure resource service

    Returns:
        Virtual network details

    Raises:
        HTTPException: If virtual network not found
    """
    vnet = await azure_service.get_virtual_network(
        subscription_id=subscription_id,
        resource_group_name=resource_group,
        vnet_name=vnet_name,
        refresh_cache=refresh_cache,
    )

    if not vnet:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Virtual network {vnet_name} not found in resource group {resource_group}",
        )

    return vnet
