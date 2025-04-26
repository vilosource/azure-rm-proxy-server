from fastapi import Depends, APIRouter, Query
from ..app.dependencies import get_azure_service
from ..core.models import ResourceGroupModel
from ..core.azure_service import AzureResourceService

router = APIRouter(
    tags=["Resource Groups"],
    prefix="/api/subscriptions/{subscription_id}/resource-groups",
)


@router.get("/", response_model=list[ResourceGroupModel])
async def list_resource_groups(
    subscription_id: str,
    refresh_cache: bool = Query(False, alias="refresh-cache"),
    azure_service: AzureResourceService = Depends(get_azure_service),
):
    return await azure_service.get_resource_groups(
        subscription_id, refresh_cache=refresh_cache
    )
