#!/usr/bin/env python3
"""
Script to create anonymized test fixtures from infra-data.

This script extracts a subset of the infra-data and anonymizes sensitive information
to create test fixtures suitable for unit testing without exposing real data.
"""

import os
import json
import shutil
import uuid
import random
import string
import argparse
from pathlib import Path
from typing import Dict, List, Any, Union, Optional


class TestFixtureCreator:
    """Creates anonymized test fixtures from infra-data."""

    # Constants for anonymization
    SUBSCRIPTION_TEMPLATE = "{purpose}-{index}"
    RESOURCE_GROUP_TEMPLATE = "{purpose}-rg-{index}"
    VM_NAME_TEMPLATE = "{purpose}-vm-{index}"
    VM_TYPES = ["Standard_D2s_v3", "Standard_D4s_v3", "Standard_B2ms", "Standard_F2s_v2"]
    REGIONS = ["eastus", "westus", "northeurope", "westeurope", "southeastasia"]

    def __init__(
        self, 
        source_dir: Union[str, Path], 
        target_dir: Union[str, Path],
        anonymize: bool = True
    ):
        """
        Initialize the test fixture creator.
        
        Args:
            source_dir: Source directory containing infra-data
            target_dir: Target directory for test fixtures
            anonymize: Whether to anonymize the data (default: True)
        """
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir)
        self.anonymize = anonymize
        
        # Create mapping dictionaries for anonymization
        self.subscription_map = {}
        self.resource_group_map = {}
        self.vm_name_map = {}
        self.ip_map = {}
        
        # Ensure target directory exists and is empty
        if self.target_dir.exists():
            shutil.rmtree(self.target_dir)
        self.target_dir.mkdir(parents=True)

    def extract_fixtures(self):
        """Extract and anonymize test fixtures from infra-data."""
        print(f"Extracting fixtures from {self.source_dir} to {self.target_dir}")
        
        # Extract subscriptions (keeping only 2)
        self._extract_subscriptions()
        
        # Extract resource groups (2 per subscription)
        self._extract_resource_groups()
        
        # Extract VMs (2 per resource group)
        self._extract_virtual_machines()
        
        # Extract route tables
        self._extract_route_tables()
        
        # Extract VM reports
        self._extract_vm_reports()
        
        print("Test fixture extraction complete!")

    def _extract_subscriptions(self):
        """Extract and anonymize subscription data."""
        subs_file = self.source_dir / "subscriptions.json"
        if not subs_file.exists():
            print(f"Warning: Subscriptions file not found at {subs_file}")
            return
            
        with open(subs_file, "r") as f:
            subscriptions = json.load(f)
        
        # Only keep 2 subscriptions for testing
        test_subscriptions = subscriptions[:2] if len(subscriptions) > 1 else subscriptions
        
        if self.anonymize:
            # Anonymize subscription data
            for i, sub in enumerate(test_subscriptions):
                original_id = sub["id"]
                purpose = "test" if i == 0 else "prod"
                
                # Create deterministic but anonymized values
                new_id = str(uuid.uuid4())
                new_name = self.SUBSCRIPTION_TEMPLATE.format(purpose=purpose, index=i+1)
                
                # Store mapping for later use
                self.subscription_map[original_id] = {
                    "new_id": new_id,
                    "new_name": new_name
                }
                
                # Update subscription object
                sub["id"] = new_id
                sub["name"] = new_name
                sub["display_name"] = new_name
        
        # Save anonymized subscriptions
        target_file = self.target_dir / "subscriptions.json"
        with open(target_file, "w") as f:
            json.dump(test_subscriptions, f, indent=2)
            
        print(f"Extracted {len(test_subscriptions)} subscriptions")
        
    def _extract_resource_groups(self):
        """Extract and anonymize resource group data."""
        subscriptions = self._read_json_file(self.target_dir / "subscriptions.json")
        if not subscriptions:
            return
            
        for i, sub in enumerate(subscriptions):
            sub_id = sub["id"]
            original_sub_id = list(self.subscription_map.keys())[i] if self.subscription_map else sub_id
            
            # Create directory for this subscription
            sub_dir = self.target_dir / "resource_groups" / sub_id
            sub_dir.mkdir(parents=True, exist_ok=True)
            
            # Find resource groups for this subscription
            rg_source_path = self.source_dir / original_sub_id
            if not rg_source_path.exists():
                print(f"Warning: No resource groups found for subscription {original_sub_id}")
                continue
                
            # Get list of resource groups (either directories or from a resource_groups.json file)
            resource_groups = []
            rg_file = rg_source_path / "resource_groups.json"
            if rg_file.exists():
                resource_groups = self._read_json_file(rg_file)
            else:
                # Assume directories are resource groups
                resource_groups = [{"name": d.name} for d in rg_source_path.iterdir() if d.is_dir()]
            
            # Only keep 2 resource groups per subscription
            test_rgs = resource_groups[:2] if len(resource_groups) > 1 else resource_groups
            
            if self.anonymize:
                # Anonymize resource group data
                for j, rg in enumerate(test_rgs):
                    original_name = rg["name"]
                    purpose = "test" if j == 0 else "prod"
                    
                    # Create deterministic but anonymized values
                    new_name = self.RESOURCE_GROUP_TEMPLATE.format(purpose=purpose, index=j+1)
                    
                    # Store mapping for later use
                    key = (original_sub_id, original_name)
                    self.resource_group_map[key] = {
                        "new_name": new_name
                    }
                    
                    # Update resource group object
                    rg["name"] = new_name
                    if "id" in rg:
                        rg["id"] = f"/subscriptions/{sub_id}/resourceGroups/{new_name}"
                        
            # Save anonymized resource groups
            for rg in test_rgs:
                rg_file = sub_dir / f"{rg['name']}.json"
                with open(rg_file, "w") as f:
                    json.dump(rg, f, indent=2)
                    
            # Also save resource group list
            rg_list_file = sub_dir / "resource_groups.json"
            with open(rg_list_file, "w") as f:
                json.dump(test_rgs, f, indent=2)
            
            print(f"Extracted {len(test_rgs)} resource groups for subscription {sub_id}")

    def _extract_virtual_machines(self):
        """Extract and anonymize virtual machine data."""
        subscriptions = self._read_json_file(self.target_dir / "subscriptions.json")
        if not subscriptions:
            return
            
        for i, sub in enumerate(subscriptions):
            sub_id = sub["id"]
            original_sub_id = list(self.subscription_map.keys())[i] if self.subscription_map else sub_id
            
            # Get resource groups for this subscription
            rg_dir = self.target_dir / "resource_groups" / sub_id
            if not rg_dir.exists():
                continue
                
            rg_files = list(rg_dir.glob("*.json"))
            rg_files = [f for f in rg_files if f.name != "resource_groups.json"]
            
            for rg_file in rg_files:
                rg = self._read_json_file(rg_file)
                if not rg:
                    continue
                    
                rg_name = rg["name"]
                # Find the original RG name
                original_rg_name = None
                for (orig_sub, orig_rg), info in self.resource_group_map.items():
                    if orig_sub == original_sub_id and info["new_name"] == rg_name:
                        original_rg_name = orig_rg
                        break
                        
                if not original_rg_name:
                    original_rg_name = rg_name
                
                # Create directory for VMs
                vm_dir = self.target_dir / "virtual_machines" / sub_id / rg_name
                vm_dir.mkdir(parents=True, exist_ok=True)
                
                # Find VMs for this resource group
                vm_source_path = self.source_dir / original_sub_id / original_rg_name
                if not vm_source_path.exists():
                    print(f"Warning: No VMs found for RG {original_rg_name}")
                    continue
                
                # Get list of VMs (files in the resource group directory)
                vm_files = list(vm_source_path.glob("*.json"))
                
                # Only keep 2 VMs per resource group
                vm_files = vm_files[:2] if len(vm_files) > 1 else vm_files
                
                for j, vm_file in enumerate(vm_files):
                    vm_data = self._read_json_file(vm_file)
                    if not vm_data:
                        continue
                    
                    # Handle both dictionary and list cases
                    if isinstance(vm_data, list):
                        # If it's a list, use the first item if available, otherwise create a new dict
                        if vm_data:
                            vm = vm_data[0] if isinstance(vm_data[0], dict) else {"data": vm_data}
                        else:
                            vm = {"name": vm_file.stem}
                        
                        # Store the original list for later
                        original_vm_list = vm_data
                    else:
                        # If it's already a dictionary, use it directly
                        vm = vm_data
                        original_vm_list = None
                        
                    original_vm_name = vm.get("name", vm_file.stem)
                    
                    if self.anonymize:
                        # Anonymize VM data
                        purpose = "test" if j == 0 else "prod"
                        new_vm_name = self.VM_NAME_TEMPLATE.format(purpose=purpose, index=j+1)
                        
                        # Store mapping for later use
                        key = (original_sub_id, original_rg_name, original_vm_name)
                        self.vm_name_map[key] = {
                            "new_name": new_vm_name
                        }
                        
                        # Update VM object
                        if isinstance(vm, dict):
                            self._anonymize_vm(vm, sub_id, rg_name, new_vm_name, original_vm_name)
                        
                        # If we had a list originally, anonymize each item in the list
                        if original_vm_list:
                            for k, item in enumerate(original_vm_list):
                                if isinstance(item, dict):
                                    self._anonymize_vm(item, sub_id, rg_name, f"{new_vm_name}-{k}", original_vm_name)
                    
                    # Save anonymized VM
                    vm_name = vm.get("name", original_vm_name) if isinstance(vm, dict) else original_vm_name
                    target_vm_file = vm_dir / f"{vm_name}.json"
                    
                    # Save either the dictionary or the original list, whichever we had
                    with open(target_vm_file, "w") as f:
                        json.dump(original_vm_list if original_vm_list else vm, f, indent=2)
                
                print(f"Extracted {len(vm_files)} VMs for resource group {rg_name}")

    def _extract_route_tables(self):
        """Extract and anonymize route table data."""
        subscriptions = self._read_json_file(self.target_dir / "subscriptions.json")
        if not subscriptions:
            return
            
        for i, sub in enumerate(subscriptions):
            sub_id = sub["id"]
            original_sub_id = list(self.subscription_map.keys())[i] if self.subscription_map else sub_id
            
            # Create directory for route tables
            rt_dir = self.target_dir / "route_tables" / sub_id
            rt_dir.mkdir(parents=True, exist_ok=True)
            
            # Find route tables for this subscription
            rt_source_path = self.source_dir / original_sub_id / "route_tables"
            if not rt_source_path.exists():
                print(f"Warning: No route tables found for subscription {original_sub_id}")
                continue
            
            # Look for route_tables.json or individual route table files
            rt_list_file = rt_source_path / "route_tables.json"
            if rt_list_file.exists():
                route_tables = self._read_json_file(rt_list_file)
                if route_tables:
                    # Only keep 2 route tables
                    test_rts = route_tables[:2] if len(route_tables) > 1 else route_tables
                    
                    if self.anonymize:
                        for j, rt in enumerate(test_rts):
                            self._anonymize_route_table(rt, sub_id, j)
                    
                    # Save route tables list
                    target_rt_file = rt_dir / "route_tables.json"
                    with open(target_rt_file, "w") as f:
                        json.dump(test_rts, f, indent=2)
                        
                    # Also save individual route table files
                    for rt in test_rts:
                        rt_name = rt.get("name", f"route-table-{j+1}")
                        # Try to find the corresponding detailed file
                        detailed_rt_file = rt_source_path / f"{rt_name}.json"
                        if detailed_rt_file.exists():
                            detailed_rt = self._read_json_file(detailed_rt_file)
                            if detailed_rt and self.anonymize:
                                self._anonymize_route_table(detailed_rt, sub_id, j, detailed=True)
                            
                            target_detailed_rt_file = rt_dir / f"{rt_name}.json"
                            with open(target_detailed_rt_file, "w") as f:
                                json.dump(detailed_rt if detailed_rt else rt, f, indent=2)
                        else:
                            # Just save the summary as the detailed file
                            target_detailed_rt_file = rt_dir / f"{rt_name}.json"
                            with open(target_detailed_rt_file, "w") as f:
                                json.dump(rt, f, indent=2)
            else:
                # Look for individual route table files
                rt_files = list(rt_source_path.glob("*.json"))
                if not rt_files:
                    print(f"Warning: No route table files found in {rt_source_path}")
                    continue
                
                # Only keep 2 route tables
                rt_files = rt_files[:2] if len(rt_files) > 1 else rt_files
                
                route_tables = []
                for j, rt_file in enumerate(rt_files):
                    rt = self._read_json_file(rt_file)
                    if not rt:
                        continue
                    
                    if self.anonymize:
                        self._anonymize_route_table(rt, sub_id, j, detailed=True)
                    
                    # Add to list
                    route_tables.append({
                        "id": rt.get("id"),
                        "name": rt.get("name", f"route-table-{j+1}"),
                        "resource_group": rt.get("resourceGroup", "test-rg-1"),
                        "location": rt.get("location", "eastus")
                    })
                    
                    # Save detailed route table
                    target_rt_file = rt_dir / rt_file.name
                    with open(target_rt_file, "w") as f:
                        json.dump(rt, f, indent=2)
                
                # Save route tables list
                if route_tables:
                    target_rt_list_file = rt_dir / "route_tables.json"
                    with open(target_rt_list_file, "w") as f:
                        json.dump(route_tables, f, indent=2)
            
            print(f"Extracted route tables for subscription {sub_id}")

    def _extract_vm_reports(self):
        """Extract and anonymize VM reports."""
        reports_source_path = self.source_dir / "reports"
        if not reports_source_path.exists():
            print(f"Warning: No reports directory found at {reports_source_path}")
            return
            
        # Create reports directory
        reports_dir = self.target_dir / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Check for VM report
        vm_report_file = reports_source_path / "virtual-machine-report.json"
        if not vm_report_file.exists():
            print(f"Warning: No VM report found at {vm_report_file}")
            return
            
        vm_report = self._read_json_file(vm_report_file)
        if not vm_report:
            return
            
        if self.anonymize:
            # Use only a few VMs from the report for testing
            if isinstance(vm_report, list) and len(vm_report) > 2:
                vm_report = vm_report[:2]
                
            # Anonymize VM report data
            self._anonymize_vm_report(vm_report)
        
        # Save anonymized VM report
        target_report_file = reports_dir / "virtual-machine-report.json"
        with open(target_report_file, "w") as f:
            json.dump(vm_report, f, indent=2)
            
        print(f"Extracted VM report")

    def _anonymize_vm(self, vm: Dict[str, Any], sub_id: str, rg_name: str, new_name: str, original_name: str):
        """Anonymize a VM object."""
        # Basic VM properties
        vm["name"] = new_name
        if "id" in vm:
            vm["id"] = f"/subscriptions/{sub_id}/resourceGroups/{rg_name}/providers/Microsoft.Compute/virtualMachines/{new_name}"
            
        # Properties that might contain the VM name
        if "hostname" in vm:
            vm["hostname"] = f"{new_name.lower()}.mydomain.local"
            
        # Anonymize IP addresses
        if "networkProfile" in vm and "networkInterfaces" in vm["networkProfile"]:
            for intf in vm["networkProfile"]["networkInterfaces"]:
                if "properties" in intf and "ipConfigurations" in intf["properties"]:
                    for ip_config in intf["properties"]["ipConfigurations"]:
                        if "properties" in ip_config:
                            props = ip_config["properties"]
                            
                            # Private IP addresses
                            if "privateIPAddress" in props:
                                orig_ip = props["privateIPAddress"]
                                props["privateIPAddress"] = self._get_anonymized_ip(orig_ip)
                            
                            # Public IP addresses
                            if "publicIPAddress" in props and "properties" in props["publicIPAddress"]:
                                pub_props = props["publicIPAddress"]["properties"]
                                if "ipAddress" in pub_props:
                                    orig_ip = pub_props["ipAddress"]
                                    pub_props["ipAddress"] = self._get_anonymized_ip(orig_ip, public=True)
        
        # Anonymize OS profile
        if "osProfile" in vm:
            os_profile = vm["osProfile"]
            if "computerName" in os_profile:
                os_profile["computerName"] = new_name.lower()
            if "adminUsername" in os_profile:
                os_profile["adminUsername"] = "testuser"
            # Remove any secrets or passwords
            if "linuxConfiguration" in os_profile and "ssh" in os_profile["linuxConfiguration"]:
                ssh_config = os_profile["linuxConfiguration"]["ssh"]
                if "publicKeys" in ssh_config:
                    for key in ssh_config["publicKeys"]:
                        if "keyData" in key:
                            key["keyData"] = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC..."
            # Remove any Windows passwords
            if "windowsConfiguration" in os_profile:
                if "password" in os_profile:
                    os_profile["password"] = "********"
        
        # Randomize but keep reasonable values for VM properties
        if "hardwareProfile" in vm:
            vm["hardwareProfile"]["vmSize"] = random.choice(self.VM_TYPES)
            
        if "location" in vm:
            vm["location"] = random.choice(self.REGIONS)

    def _anonymize_route_table(self, rt: Dict[str, Any], sub_id: str, index: int, detailed: bool = False):
        """Anonymize a route table object."""
        # Basic properties
        rt_name = f"test-rt-{index+1}"
        rt["name"] = rt_name
        
        if "id" in rt:
            rg_name = rt.get("resourceGroup", "test-rg-1")
            rt["id"] = f"/subscriptions/{sub_id}/resourceGroups/{rg_name}/providers/Microsoft.Network/routeTables/{rt_name}"
        
        if "location" in rt:
            rt["location"] = random.choice(self.REGIONS)
            
        # Anonymize routes in detailed route tables
        if detailed and "properties" in rt and "routes" in rt["properties"]:
            for i, route in enumerate(rt["properties"]["routes"]):
                # Keep meaningful address prefixes but make them test data
                if "properties" in route and "addressPrefix" in route["properties"]:
                    orig_prefix = route["properties"]["addressPrefix"]
                    octets = orig_prefix.split('/')
                    if len(octets) == 2:
                        # Keep the CIDR notation but change the actual IP
                        cidr = octets[1]
                        route["properties"]["addressPrefix"] = f"192.168.{i}.0/{cidr}"
                        
                # Set a simple name for the route
                if "name" in route:
                    route["name"] = f"route-{i+1}"
                    
                # Set the route type to something standard
                if "properties" in route and "nextHopType" in route["properties"]:
                    # Keep the original next hop type as it's important for testing
                    pass

    def _anonymize_vm_report(self, vm_report: Union[List[Dict[str, Any]], Dict[str, Any]]):
        """Anonymize VM report data."""
        if isinstance(vm_report, list):
            for i, vm_entry in enumerate(vm_report):
                self._anonymize_vm_report_entry(vm_entry, i)
        elif isinstance(vm_report, dict):
            for i, (key, vm_entry) in enumerate(vm_report.items()):
                if isinstance(vm_entry, dict):
                    self._anonymize_vm_report_entry(vm_entry, i)

    def _anonymize_vm_report_entry(self, vm_entry: Dict[str, Any], index: int):
        """Anonymize a single VM report entry."""
        # Generate consistent anonymized values
        vm_name = f"test-vm-{index+1}"
        rg_name = f"test-rg-{index % 2 + 1}"
        sub_name = f"test-sub-{index % 2 + 1}"
        sub_id = str(uuid.uuid4())
        
        # Update VM entry with anonymized values
        for field in ["vmName", "name", "computerName"]:
            if field in vm_entry:
                vm_entry[field] = vm_name
                
        if "resourceGroup" in vm_entry:
            vm_entry["resourceGroup"] = rg_name
            
        if "subscriptionId" in vm_entry:
            vm_entry["subscriptionId"] = sub_id
            
        if "subscriptionName" in vm_entry:
            vm_entry["subscriptionName"] = sub_name
            
        # Anonymize network information
        for field in ["privateIPs", "publicIPs"]:
            if field in vm_entry and isinstance(vm_entry[field], list):
                vm_entry[field] = [
                    self._get_anonymized_ip(ip, public=(field == "publicIPs")) 
                    for ip in vm_entry[field]
                ]
                
        # Simplify network interfaces
        if "networkInterfaces" in vm_entry and isinstance(vm_entry["networkInterfaces"], list):
            for i, intf in enumerate(vm_entry["networkInterfaces"]):
                intf_name = f"{vm_name}-nic-{i+1}"
                if isinstance(intf, dict):
                    intf["name"] = intf_name
                    if "id" in intf:
                        intf["id"] = f"/subscriptions/{sub_id}/resourceGroups/{rg_name}/providers/Microsoft.Network/networkInterfaces/{intf_name}"
                        
                    # Anonymize IP configurations
                    if "ipConfigurations" in intf and isinstance(intf["ipConfigurations"], list):
                        for j, ip_config in enumerate(intf["ipConfigurations"]):
                            if isinstance(ip_config, dict):
                                ip_config_name = f"ipconfig{j+1}"
                                ip_config["name"] = ip_config_name
                                
                                if "privateIPAddress" in ip_config:
                                    ip_config["privateIPAddress"] = self._get_anonymized_ip(ip_config["privateIPAddress"])
                                    
                                if "publicIPAddress" in ip_config and isinstance(ip_config["publicIPAddress"], dict):
                                    if "ipAddress" in ip_config["publicIPAddress"]:
                                        ip_config["publicIPAddress"]["ipAddress"] = self._get_anonymized_ip(
                                            ip_config["publicIPAddress"]["ipAddress"], 
                                            public=True
                                        )
                                        
        # Anonymize OS information but keep the OS type the same
        if "osType" in vm_entry:
            # Keep OS type (Windows/Linux) as it's important for testing
            pass
            
        if "size" in vm_entry:
            vm_entry["size"] = random.choice(self.VM_TYPES)
            
        if "location" in vm_entry:
            vm_entry["location"] = random.choice(self.REGIONS)

    def _get_anonymized_ip(self, original_ip: str, public: bool = False) -> str:
        """
        Get an anonymized IP address that consistently maps to the original.
        
        Args:
            original_ip: The original IP address
            public: Whether this is a public IP address
            
        Returns:
            An anonymized IP address
        """
        # If we've already anonymized this IP, return the same value
        if original_ip in self.ip_map:
            return self.ip_map[original_ip]
            
        if public:
            # For public IPs, use ranges that would never be used in real systems
            prefix = "203.0.113"  # TEST-NET-3 range
        else:
            # For private IPs, use typical private ranges
            prefix = "192.168"
            
        # Generate deterministic last octets
        ip_hash = hash(original_ip) % 256
        last_octet = abs(ip_hash)
            
        # Create a consistent mapping
        new_ip = f"{prefix}.{len(self.ip_map) % 256}.{last_octet}"
        self.ip_map[original_ip] = new_ip
            
        return new_ip

    def _read_json_file(self, file_path: Path) -> Optional[Any]:
        """Read a JSON file and return its contents."""
        try:
            if file_path.exists():
                with open(file_path, "r") as f:
                    return json.load(f)
            return None
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return None


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Create anonymized test fixtures from infra-data")
    parser.add_argument(
        "--source", 
        default=None,
        help="Source directory containing infra-data (default: infra-data or most recent infra-data-*)"
    )
    parser.add_argument(
        "--target", 
        default="azure_rm_client/tests/fixtures",
        help="Target directory for test fixtures"
    )
    parser.add_argument(
        "--no-anonymize", 
        action="store_true",
        help="Don't anonymize the data (not recommended for test fixtures)"
    )
    
    args = parser.parse_args()
    
    # Find source directory if not specified
    source_dir = args.source
    if not source_dir:
        # Try standard directory first
        if os.path.exists("infra-data"):
            source_dir = "infra-data"
        else:
            # Look for dated versions
            infra_dirs = [d for d in os.listdir('.') if os.path.isdir(d) and d.startswith("infra-data-")]
            if infra_dirs:
                # Use most recent directory
                infra_dirs.sort(reverse=True)
                source_dir = infra_dirs[0]
                
    if not source_dir or not os.path.exists(source_dir):
        print("Error: Could not find infra-data directory. Please specify with --source.")
        return 1
        
    creator = TestFixtureCreator(
        source_dir=source_dir,
        target_dir=args.target,
        anonymize=not args.no_anonymize
    )
    
    creator.extract_fixtures()
    return 0


if __name__ == "__main__":
    exit(main())