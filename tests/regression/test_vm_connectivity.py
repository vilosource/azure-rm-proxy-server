"""
Test the VM connectivity tool.
"""

import os
import unittest
import tempfile
import json
import networkx as nx
from azure_rm_network_tool.vm_connectivity import parse_vm_data, build_graph, check_connectivity


class TestVMConnectivity(unittest.TestCase):
    """Test the VM connectivity functionality."""

    def setUp(self):
        """Set up test data."""
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()

        # Create test VM data
        self.vm1_data = {
            "name": "vm1",
            "network_interfaces": [{"private_ip_addresses": ["10.0.0.4"]}],
            "effective_routes": [
                {"address_prefix": "10.0.0.0/24", "next_hop_type": "VnetLocal"},
                {"address_prefix": "172.20.4.0/22", "next_hop_type": "VirtualNetworkGateway"},
            ],
        }

        self.vm2_data = {
            "name": "vm2",
            "network_interfaces": [{"private_ip_addresses": ["10.0.0.5"]}],
            "effective_routes": [{"address_prefix": "10.0.0.0/24", "next_hop_type": "VnetLocal"}],
        }

        self.vm3_data = {
            "name": "vm3",
            "network_interfaces": [{"private_ip_addresses": ["172.20.5.10"]}],
            "effective_routes": [{"address_prefix": "172.20.4.0/22", "next_hop_type": "VnetLocal"}],
        }

        # Write VM data to files
        for vm_data in [self.vm1_data, self.vm2_data, self.vm3_data]:
            vm_file = os.path.join(self.test_dir, f"vm_{vm_data['name']}.json")
            with open(vm_file, "w") as f:
                json.dump(vm_data, f)

    def test_parse_vm_data(self):
        """Test parsing VM data from files."""
        vm_data = parse_vm_data(self.test_dir)
        self.assertEqual(len(vm_data), 3)
        self.assertIn("vm1", vm_data)
        self.assertIn("vm2", vm_data)
        self.assertIn("vm3", vm_data)

    def test_build_graph(self):
        """Test building the network graph."""
        vm_data = parse_vm_data(self.test_dir)
        gateway_ip = "20.240.246.240"
        gateway_routes = [
            {"address_prefix": "172.20.4.0/22", "next_hop_type": "VirtualNetworkGateway"}
        ]

        G = build_graph(vm_data, gateway_ip, gateway_routes)

        # Check nodes
        self.assertEqual(len(G.nodes), 4)  # 3 VMs + 1 Gateway
        self.assertIn("vm1", G.nodes)
        self.assertIn("vm2", G.nodes)
        self.assertIn("vm3", G.nodes)
        self.assertIn("VirtualNetworkGateway", G.nodes)

        # Check edges
        self.assertGreaterEqual(len(G.edges), 3)  # At least 3 edges should exist

    def test_check_connectivity_direct(self):
        """Test connectivity check between VMs on the same subnet."""
        vm_data = parse_vm_data(self.test_dir)
        gateway_ip = "20.240.246.240"
        gateway_routes = [
            {"address_prefix": "172.20.4.0/22", "next_hop_type": "VirtualNetworkGateway"}
        ]

        G = build_graph(vm_data, gateway_ip, gateway_routes)

        # VMs on the same subnet should be connected
        reachable, path = check_connectivity(G, "vm1", "vm2")
        self.assertTrue(reachable)
        self.assertEqual(path, ["vm1", "vm2"])

    def test_check_connectivity_through_gateway(self):
        """Test connectivity check between VMs through a gateway."""
        vm_data = parse_vm_data(self.test_dir)
        gateway_ip = "20.240.246.240"
        gateway_routes = [
            {"address_prefix": "172.20.4.0/22", "next_hop_type": "VirtualNetworkGateway"}
        ]

        G = build_graph(vm_data, gateway_ip, gateway_routes)

        # VMs connected through gateway
        reachable, path = check_connectivity(G, "vm1", "vm3")
        self.assertTrue(reachable)
        self.assertEqual(len(path), 3)  # vm1 -> Gateway -> vm3
        self.assertEqual(path[0], "vm1")
        self.assertEqual(path[1], "VirtualNetworkGateway")
        self.assertEqual(path[2], "vm3")

    def tearDown(self):
        """Clean up temporary test files."""
        # Remove test files
        for vm_name in ["vm1", "vm2", "vm3"]:
            vm_file = os.path.join(self.test_dir, f"vm_{vm_name}.json")
            if os.path.exists(vm_file):
                os.remove(vm_file)

        # Remove test directory
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)


if __name__ == "__main__":
    unittest.main()
