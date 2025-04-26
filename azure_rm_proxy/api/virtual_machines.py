from fastapi import Depends, APIRouter, Query, HTTPException
from ..app.dependencies import get_azure_service
from ..core.models import VirtualMachineModel, VirtualMachineDetail
from ..core.azure_service import AzureResourceService
from azure.core.exceptions import ResourceNotFoundError, ClientAuthenticationError

router = APIRouter(
    tags=["Virtual Machines"],
    prefix="/api/subscriptions/{subscription_id}/resource-groups/{resource_group_name}/virtual-machines",
)


@router.get("/", response_model=list[VirtualMachineModel])
async def list_virtual_machines(
    subscription_id: str,
    resource_group_name: str,
    refresh_cache: bool = Query(False, alias="refresh-cache"),
    azure_service: AzureResourceService = Depends(get_azure_service),
):
    return await azure_service.get_virtual_machines(
        subscription_id, resource_group_name, refresh_cache=refresh_cache
    )


@router.get("/{vm_name}", response_model=VirtualMachineDetail)
async def get_virtual_machine_details(
    subscription_id: str,
    resource_group_name: str,
    vm_name: str,
    refresh_cache: bool = Query(False, alias="refresh-cache"),
    azure_service: AzureResourceService = Depends(get_azure_service),
):
    try:
        return await azure_service.get_vm_details(
            subscription_id, resource_group_name, vm_name, refresh_cache=refresh_cache
        )
    except ResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Virtual Machine not found")
    except ClientAuthenticationError:
        raise HTTPException(status_code=401, detail="Authentication failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
