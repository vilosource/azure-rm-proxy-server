from fastapi import Depends, APIRouter, Query, HTTPException
from ..app.dependencies import get_azure_service
from ..core.models import VirtualMachineWithContext, VirtualMachineDetail
from ..core.azure_service import AzureResourceService
from azure.core.exceptions import ResourceNotFoundError, ClientAuthenticationError

router = APIRouter(tags=["VM Shortcuts"], prefix="/api/subscriptions/virtual_machines")


@router.get("/", response_model=list[VirtualMachineWithContext])
async def list_all_virtual_machines(
    refresh_cache: bool = Query(False, alias="refresh-cache"),
    azure_service: AzureResourceService = Depends(get_azure_service),
):
    """
    Get all virtual machines across all subscriptions and resource groups.
    This is a convenience endpoint that avoids navigating through subscriptions and resource groups.
    """
    try:
        # Get all VMs from the service
        vms = await azure_service.get_all_virtual_machines(refresh_cache=refresh_cache)

        # Add detail_url to each VM
        for vm in vms:
            vm.detail_url = f"/api/subscriptions/virtual_machines/{vm.name}"

        return vms
    except ClientAuthenticationError:
        raise HTTPException(status_code=401, detail="Authentication failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@router.get("/{vm_name}", response_model=VirtualMachineDetail)
async def get_vm_by_name(
    vm_name: str,
    refresh_cache: bool = Query(False, alias="refresh-cache"),
    debug: bool = Query(False, alias="debug"),
    azure_service: AzureResourceService = Depends(get_azure_service),
):
    """
    Find a virtual machine by name across all subscriptions and resource groups.
    This is a convenience endpoint that avoids needing to know the subscription and resource group.

    Parameters:
        vm_name: Name of the VM to find
        refresh_cache: Whether to bypass cache and fetch fresh data
        debug: Enable extra debug logging for troubleshooting
    """
    try:
        if debug:
            # Force log level to DEBUG temporarily
            import logging

            root_logger = logging.getLogger("azure_rm_proxy")
            original_level = root_logger.level
            root_logger.setLevel(logging.DEBUG)

            # Always refresh cache in debug mode
            result = await azure_service.find_vm_by_name(vm_name, refresh_cache=True)

            # Restore original log level
            root_logger.setLevel(original_level)
            return result
        else:
            return await azure_service.find_vm_by_name(
                vm_name, refresh_cache=refresh_cache
            )
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Virtual Machine '{vm_name}' not found in any subscription or resource group",
        )
    except ClientAuthenticationError:
        raise HTTPException(status_code=401, detail="Authentication failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
