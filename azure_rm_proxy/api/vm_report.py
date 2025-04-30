from fastapi import Depends, APIRouter, Query, HTTPException
from ..app.dependencies import get_azure_service
from ..core.models import VirtualMachineReport
from ..core.azure_service import AzureResourceService
from azure.core.exceptions import ResourceNotFoundError, ClientAuthenticationError
from typing import List

router = APIRouter(tags=["VM Report"], prefix="/api/reports")


@router.get("/virtual-machines", response_model=List[VirtualMachineReport])
async def get_vm_report(
    refresh_cache: bool = Query(False, alias="refresh-cache"),
    azure_service: AzureResourceService = Depends(get_azure_service),
):
    """
    Generate a comprehensive report of all virtual machines across all subscriptions.

    The report includes detailed information about each VM:
    - Hostname (if available)
    - Operating System
    - Environment (from tags)
    - Purpose (from tags)
    - Private IP Addresses
    - Public IP Addresses
    - VM Name
    - VM Size
    - OS Disk Size (GB)
    - Resource Group
    - Location
    - Subscription Information

    Parameters:
        refresh_cache: When set to true, bypasses cache and retrieves fresh data from Azure
    """
    try:
        return await azure_service.get_vm_report(refresh_cache=refresh_cache)
    except ClientAuthenticationError:
        raise HTTPException(status_code=401, detail="Authentication failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
