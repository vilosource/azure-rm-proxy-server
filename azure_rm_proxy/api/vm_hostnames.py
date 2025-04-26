from fastapi import Depends, APIRouter, Query, HTTPException
from ..app.dependencies import get_azure_service
from ..core.models import VirtualMachineHostname
from ..core.azure_service import AzureResourceService
from azure.core.exceptions import ResourceNotFoundError, ClientAuthenticationError

router = APIRouter(tags=["VM Hostnames"], prefix="/api/subscriptions/hostnames")


@router.get("/", response_model=list[VirtualMachineHostname])
async def list_vm_hostnames(
    subscription_id: str = Query(None, alias="subscription-id"),
    refresh_cache: bool = Query(False, alias="refresh-cache"),
    azure_service: AzureResourceService = Depends(get_azure_service),
):
    """
    Get a list of VM names and their hostnames from tags.
    This endpoint is equivalent to the Azure CLI command:
    az vm list --subscription <your-subscription-id> --query "[].{VMName:name, Hostname:tags.hostname}" --output tsv

    Parameters:
        subscription_id: Optional subscription ID to filter by. If None, gets VMs from all subscriptions.
        refresh_cache: Whether to bypass cache and fetch fresh data
    """
    try:
        return await azure_service.get_vm_hostnames(
            subscription_id, refresh_cache=refresh_cache
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ClientAuthenticationError:
        raise HTTPException(status_code=401, detail="Authentication failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
