from typing import List, Optional
from pydantic import BaseModel

class SubscriptionModel(BaseModel):
    id: str
    name: str
    display_name: Optional[str] = None
    state: str

class ResourceGroupModel(BaseModel):
    id: str
    name: str
    location: str
    tags: Optional[dict] = None

class NetworkInterfaceModel(BaseModel):
    id: str
    name: str
    private_ip_addresses: List[str]
    public_ip_addresses: List[str]

class NsgRuleModel(BaseModel):
    name: str
    direction: str
    protocol: str
    port_range: str
    access: str

class RouteModel(BaseModel):
    address_prefix: str
    next_hop_type: str
    next_hop_ip: Optional[str] = None
    route_origin: str

class AADGroupModel(BaseModel):
    id: str
    display_name: Optional[str] = None

class VirtualMachineModel(BaseModel):
    id: str
    name: str
    location: str
    vm_size: str
    os_type: Optional[str] = None
    power_state: Optional[str] = None

class VirtualMachineDetail(VirtualMachineModel):
    network_interfaces: List[NetworkInterfaceModel]
    effective_nsg_rules: List[NsgRuleModel]
    effective_routes: List[RouteModel]
    aad_groups: List[AADGroupModel]

class VirtualMachineWithContext(VirtualMachineModel):
    """Extended virtual machine model that includes subscription and resource group context"""
    subscription_id: Optional[str] = None 
    subscription_name: Optional[str] = None
    resource_group_name: Optional[str] = None
    detail_url: Optional[str] = None

class VirtualMachineHostname(BaseModel):
    """Model for VM name and hostname"""
    vm_name: str
    hostname: Optional[str] = None
