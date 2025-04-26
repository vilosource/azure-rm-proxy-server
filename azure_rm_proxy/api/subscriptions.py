from fastapi import Depends, APIRouter, Query
from ..app.dependencies import get_azure_service
from ..core.models import SubscriptionModel
from ..core.azure_service import AzureResourceService

router = APIRouter(tags=["Subscriptions"], prefix="/api/subscriptions")


@router.get("/", response_model=list[SubscriptionModel])
async def list_subscriptions(
    refresh_cache: bool = Query(False, alias="refresh-cache"),
    azure_service: AzureResourceService = Depends(get_azure_service),
):
    return await azure_service.get_subscriptions(refresh_cache=refresh_cache)
