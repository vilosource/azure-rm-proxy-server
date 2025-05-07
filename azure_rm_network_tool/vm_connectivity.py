"""
Azure VM Connectivity Analyzer

This module uses NetworkX to analyze connectivity between Azure VMs based on route information.
"""

import os
import json
import networkx as nx
import ipaddress
import argparse
from typing import Dict, Tuple, List, Any


# Function to parse VM data from JSON files
def parse_vm_data(infra_folder: str) -> Dict[str, Any]:
    """
    Parse VM data from JSON files in the specified folder.

    Args:
        infra_folder: Path to the folder containing VM JSON data

    Returns:
        Dictionary of VM data keyed by VM name
    """
    vm_data = {}
    for root, dirs, files in os.walk(infra_folder):
        for file in files:
            if file.startswith("vm_") and file.endswith(".json"):
                path = os.path.join(root, file)
                with open(path, "r") as f:
                    try:
                        vm = json.load(f)
                        if "name" in vm and "network_interfaces" in vm:
                            vm_data[vm["name"]] = vm
                    except json.JSONDecodeError:
                        print(f"Warning: Could not parse JSON in {path}")
    return vm_data


# Create the network graph including gateway nodes
def build_graph(
    vm_data: Dict[str, Any], gateway_ip: str, gateway_routes: List[Dict[str, str]]
) -> nx.DiGraph:
    """
    Build a directed graph representing the network topology.

    Args:
        vm_data: Dictionary of VM data
        gateway_ip: IP address of the virtual network gateway
        gateway_routes: List of routes configured on the gateway

    Returns:
        NetworkX directed graph representing the network
    """
    G = nx.DiGraph()

    # Add VM nodes
    for vm_name, vm in vm_data.items():
        if "network_interfaces" in vm and len(vm["network_interfaces"]) > 0:
            private_ips = vm["network_interfaces"][0].get("private_ip_addresses", [])
            G.add_node(vm_name, ips=private_ips)

    # Add Gateway node explicitly
    gateway_name = "VirtualNetworkGateway"
    G.add_node(gateway_name, ips=[gateway_ip])

    # VM-to-Gateway edges
    for vm_name, vm in vm_data.items():
        for route in vm.get("effective_routes", []):
            if route["next_hop_type"] == "VirtualNetworkGateway":
                G.add_edge(vm_name, gateway_name, prefix=route["address_prefix"])

    # Gateway-to-VM edges based on gateway routes
    for route in gateway_routes:
        route_net = ipaddress.ip_network(route["address_prefix"])
        for vm_name, vm in vm_data.items():
            if "network_interfaces" in vm and len(vm["network_interfaces"]) > 0:
                vm_ips = vm["network_interfaces"][0].get("private_ip_addresses", [])
                if any(ip and ipaddress.ip_address(ip) in route_net for ip in vm_ips):
                    G.add_edge(gateway_name, vm_name, prefix=route["address_prefix"])

    # Direct VM-to-VM edges based on VNet local routes
    for vm_name, vm in vm_data.items():
        for route in vm.get("effective_routes", []):
            if route["next_hop_type"] == "VnetLocal":
                route_net = ipaddress.ip_network(route["address_prefix"])
                for other_vm, other_vm_data in vm_data.items():
                    if vm_name != other_vm and "network_interfaces" in other_vm_data:
                        other_ips = other_vm_data["network_interfaces"][0].get(
                            "private_ip_addresses", []
                        )
                        if any(ip and ipaddress.ip_address(ip) in route_net for ip in other_ips):
                            G.add_edge(vm_name, other_vm, prefix=route["address_prefix"])

    return G


# Function to check path connectivity
def check_connectivity(G: nx.DiGraph, source_vm: str, dest_vm: str) -> Tuple[bool, List[str]]:
    """
    Check if there's a path from source_vm to dest_vm in the graph.

    Args:
        G: NetworkX graph representing the network
        source_vm: Source VM name
        dest_vm: Destination VM name

    Returns:
        Tuple of (reachable, path) where reachable is a boolean and path is a list of node names
    """
    try:
        path = nx.shortest_path(G, source_vm, dest_vm)
        return True, path
    except nx.NetworkXNoPath:
        return False, []
    except nx.NodeNotFound as e:
        print(f"Error: VM not found in graph: {e}")
        return False, []


def main():
    """Main function to run the connectivity analysis from command line"""
    parser = argparse.ArgumentParser(description="Check Azure VM network connectivity.")
    parser.add_argument("-s", "--source-vm", required=True, help="Source VM name")
    parser.add_argument("-d", "--destination-vm", required=True, help="Destination VM name")
    parser.add_argument("-f", "--folder", required=True, help="Path to infrastructure data folder")
    parser.add_argument(
        "-g", "--gateway-ip", default="20.240.246.240", help="Virtual Network Gateway IP"
    )
    parser.add_argument("-r", "--routes-file", help="Path to gateway routes JSON file")

    args = parser.parse_args()

    # Load VM data
    vm_data = parse_vm_data(args.folder)
    if not vm_data:
        print("Error: No VM data found in the specified folder")
        return

    # Load gateway routes
    gateway_routes = []
    if args.routes_file:
        try:
            with open(args.routes_file, "r") as f:
                gateway_routes = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading gateway routes: {e}")
            gateway_routes = [
                {"address_prefix": "172.20.4.0/22", "next_hop_type": "VirtualNetworkGateway"},
                {"address_prefix": "10.0.0.0/8", "next_hop_type": "VirtualNetworkGateway"},
            ]
    else:
        # Default gateway routes
        gateway_routes = [
            {"address_prefix": "172.20.4.0/22", "next_hop_type": "VirtualNetworkGateway"},
            {"address_prefix": "10.0.0.0/8", "next_hop_type": "VirtualNetworkGateway"},
        ]

    # Build network graph
    G = build_graph(vm_data, args.gateway_ip, gateway_routes)

    # Check connectivity
    reachable, path = check_connectivity(G, args.source_vm, args.destination_vm)

    if reachable:
        print(f"✅ Connectivity confirmed! Path:")
        for hop, node in enumerate(path, 1):
            ips = G.nodes[node]["ips"]
            print(f"Hop {hop}: {node} | IPs: {', '.join(ips)}")
    else:
        print("❌ No connectivity path found between the specified VMs.")


if __name__ == "__main__":
    main()
