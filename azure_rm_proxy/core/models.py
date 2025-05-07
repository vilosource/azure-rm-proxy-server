from typing import List, Optional, Dict
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


class RouteEntryModel(BaseModel):
    """Model for a route entry within a route table"""

    name: str
    address_prefix: str
    next_hop_type: str
    next_hop_ip_address: Optional[str] = None


class RouteTableSummaryModel(BaseModel):
    """Summary model for a route table"""

    id: str
    name: str
    location: str
    resource_group: str
    route_count: int
    subnet_count: int
    provisioning_state: str
    subscription_id: Optional[str] = None


class RouteTableModel(BaseModel):
    """Detailed model for a route table"""

    id: str
    name: str
    location: str
    resource_group: str
    routes: List[RouteEntryModel]
    subnets: List[str] = []
    provisioning_state: str
    disable_bgp_route_propagation: bool = False
    tags: Optional[Dict[str, str]] = None
    subscription_id: Optional[str] = None


class ServiceEndpointModel(BaseModel):
    """Model for service endpoint information"""

    service: str
    locations: List[str] = []
    provisioning_state: Optional[str] = None


class SubnetModel(BaseModel):
    """Model for subnet information"""

    id: str
    name: str
    address_prefix: str
    network_security_group_id: Optional[str] = None
    route_table_id: Optional[str] = None
    provisioning_state: str
    private_endpoint_network_policies: Optional[str] = None
    private_link_service_network_policies: Optional[str] = None
    service_endpoints: List[ServiceEndpointModel] = []


class VirtualNetworkPeeringModel(BaseModel):
    """Model for virtual network peering information"""

    id: str
    name: str
    remote_virtual_network_id: str
    allow_virtual_network_access: bool = True
    allow_forwarded_traffic: bool = False
    allow_gateway_transit: bool = False
    use_remote_gateways: bool = False
    peering_state: str
    provisioning_state: str


class VirtualNetworkPeeringPairModel(BaseModel):
    """Model for a virtual network peering pair (both sides of connection)"""

    peering_id: str  # Unique identifier for this peering pair
    vnet1_id: str
    vnet1_name: str
    vnet1_resource_group: str
    vnet1_subscription_id: str
    vnet1_to_vnet2_state: str  # Peering state from vnet1 to vnet2

    vnet2_id: str
    vnet2_name: str
    vnet2_resource_group: str
    vnet2_subscription_id: str
    vnet2_to_vnet1_state: str  # Peering state from vnet2 to vnet1

    allow_virtual_network_access: bool = True
    allow_forwarded_traffic: bool = False
    allow_gateway_transit: bool = False
    use_remote_gateways: bool = False

    provisioning_state: str
    connected: bool  # True if peering is fully established in both directions


class VirtualNetworkModel(BaseModel):
    """Model for virtual network information"""

    id: str
    name: str
    location: str
    resource_group: str
    address_space: List[str]
    dns_servers: List[str] = []
    subnets: List[SubnetModel] = []
    peerings: List[VirtualNetworkPeeringModel] = []
    enable_ddos_protection: bool = False
    tags: Optional[Dict[str, str]] = None
    provisioning_state: str
    subscription_id: Optional[str] = None


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


class VirtualMachineReport(BaseModel):
    """Model for VM report with detailed information"""

    hostname: Optional[str] = None
    os: Optional[str] = None
    environment: Optional[str] = None
    purpose: Optional[str] = None
    ip_addresses: List[str] = []
    public_ip_addresses: List[str] = []
    vm_name: str
    vm_size: str
    os_disk_size_gb: Optional[float] = None
    resource_group: str
    location: str
    subscription_id: str
    subscription_name: Optional[str] = None
