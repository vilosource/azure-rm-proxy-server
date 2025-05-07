"""API endpoints for virtual network peering reports."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from ..app.dependencies import get_azure_service
from ..core.models import VirtualNetworkPeeringPairModel
from ..core.azure_service import AzureResourceService

router = APIRouter(tags=["Virtual Network Peerings"], prefix="/api/vnet-peering-report")


@router.get(
    "/subscriptions/{subscription_id}",
    response_model=List[VirtualNetworkPeeringPairModel],
    summary="Get virtual network peering report for a subscription",
    description="Returns a report of all virtual network peerings in the specified subscription, showing both sides of each connection.",
)
async def get_subscription_peering_report(
    subscription_id: str,
    resource_group: Optional[str] = Query(None, description="Filter by resource group"),
    refresh_cache: bool = Query(False, alias="refresh-cache", description="Whether to bypass cache and fetch fresh data"),
    azure_service: AzureResourceService = Depends(get_azure_service),
) -> List[VirtualNetworkPeeringPairModel]:
    """
    Get a report of all virtual network peerings in a subscription.
    
    This report shows paired relationships between virtual networks, including status on both sides of the connection.
    
    Args:
        subscription_id: Azure subscription ID
        resource_group: Optional resource group name to filter by
        refresh_cache: Whether to bypass cache and fetch fresh data
        azure_service: Azure resource service

    Returns:
        List of virtual network peering pairs
    """
    return await azure_service.get_peering_report(
        subscription_id=subscription_id,
        resource_group_name=resource_group,
        refresh_cache=refresh_cache,
    )