#!/usr/bin/env python3
"""
Integration Test for Azure RM Proxy Server

This script performs end-to-end integration testing by:
1. Starting the API server in a separate process
2. Testing all API endpoints
3. Validating responses and data structures
4. Generating a test report
5. Stopping the server

Usage:
    python -m azure_rm_proxy.tests.scripts.integration_test [--mock] [--host HOST] [--port PORT]
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
import datetime
import subprocess
import signal
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import html
import uuid

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Adjust path to include project root
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

# Global settings
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 8000
DEFAULT_TIMEOUT = 30  # seconds
REPORT_DIR = Path(__file__).resolve().parents[3] / "test_reports"


class EndpointTest:
    """Class to track and report on an individual endpoint test"""

    def __init__(self, name: str, url: str, method: str = "GET", params: Dict = None):
        self.name = name
        self.url = url
        self.method = method
        self.params = params or {}
        self.start_time = None
        self.end_time = None
        self.duration = None
        self.status_code = None
        self.response_size = None
        self.success = False
        self.error = None
        self.validation_results = []

    def start(self):
        """Mark the start time of the test"""
        self.start_time = time.time()

    def complete(
        self, response: requests.Response, success: bool, error: Optional[str] = None
    ):
        """Record test completion details"""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.status_code = response.status_code if response else None
        self.response_size = len(response.content) if response else 0
        self.success = success
        self.error = error

    def add_validation(self, name: str, success: bool, details: str = ""):
        """Add a validation result"""
        self.validation_results.append(
            {"name": name, "success": success, "details": details}
        )

    def as_dict(self) -> Dict:
        """Convert to dictionary for reporting"""
        return {
            "name": self.name,
            "url": self.url,
            "method": self.method,
            "params": self.params,
            "duration": f"{self.duration:.4f}s" if self.duration else None,
            "status_code": self.status_code,
            "response_size": (
                f"{self.response_size/1024:.2f} KB" if self.response_size else None
            ),
            "success": self.success,
            "error": self.error,
            "validations": self.validation_results,
        }


class APIIntegrationTest:
    """Main class for running API integration tests"""

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        use_mock: bool = False,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.api_url = f"{self.base_url}/api"
        self.use_mock = use_mock
        self.timeout = timeout
        self.server_process = None
        self.tests = []
        self.test_results = []
        self.session = requests.Session()
        self.start_time = None
        self.end_time = None
        self.test_id = str(uuid.uuid4())[:8]

    def start_server(self) -> bool:
        """Start the API server as a subprocess"""
        logger.info(f"Starting API server on {self.host}:{self.port}...")

        cmd = [
            "python",
            "-m",
            "azure_rm_proxy.app.main",
            "--host",
            self.host,
            "--port",
            str(self.port),
        ]

        if self.use_mock:
            os.environ["USE_MOCK"] = "true"
            logger.info("Using mock service")

        try:
            # Start server as a subprocess
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )

            # Wait for server to start up
            start_time = time.time()
            server_ready = False

            while time.time() - start_time < self.timeout:
                try:
                    response = requests.get(f"{self.api_url}/ping", timeout=0.5)
                    if response.status_code == 200:
                        logger.info("Server started successfully")
                        server_ready = True
                        break
                except requests.exceptions.RequestException:
                    # Server not ready yet, wait and retry
                    time.sleep(0.5)

            if not server_ready:
                logger.error(f"Server failed to start within {self.timeout} seconds")
                self.stop_server()
                return False

            return True

        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            if self.server_process:
                self.stop_server()
            return False

    def stop_server(self):
        """Stop the API server subprocess"""
        if self.server_process:
            logger.info("Stopping API server...")

            # Try to terminate gracefully first
            self.server_process.terminate()

            # Give it some time to shutdown
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Server did not terminate gracefully, forcing...")
                self.server_process.kill()

            # Collect output for debugging
            stdout, stderr = self.server_process.communicate()
            if stdout:
                logger.debug(f"Server stdout: {stdout}")
            if stderr:
                logger.debug(f"Server stderr: {stderr}")

            self.server_process = None
            logger.info("Server stopped")

    def run_tests(self):
        """Run all API endpoint tests"""
        self.start_time = time.time()

        try:
            # Skip these if server already running externally
            if not self.server_process and not self.start_server():
                return False

            # Test health endpoint
            self.test_ping()

            # Test subscriptions endpoint
            subscriptions = self.test_subscriptions()
            if not subscriptions:
                logger.warning("No subscriptions found, can't test dependent endpoints")
                return True

            # Choose first subscription for further testing
            sub_id = subscriptions[0].get("id")
            logger.info(f"Using subscription {sub_id} for further tests")

            # Test resource groups endpoint
            resource_groups = self.test_resource_groups(sub_id)
            if not resource_groups:
                logger.warning(f"No resource groups found in subscription {sub_id}")
            else:
                # Choose first resource group for further testing
                rg_name = resource_groups[0].get("name")
                logger.info(f"Using resource group {rg_name} for further tests")

                # Test virtual machines endpoints
                vms, vm_detail = self.test_virtual_machines(sub_id, rg_name)
                
                # Test route table endpoints
                route_tables = self.test_route_tables(sub_id)
                if route_tables and len(route_tables) > 0:
                    # Test route table details endpoint with the first route table
                    rt_name = route_tables[0].get("name")
                    rt_resource_group = route_tables[0].get("resource_group")
                    logger.info(f"Using route table {rt_name} for further tests")
                    
                    self.test_route_table_details(sub_id, rt_resource_group, rt_name)
                    
                    # If we have VM details, test VM routes endpoint
                    if vms and len(vms) > 0:
                        vm_name = vms[0].get("name")
                        self.test_vm_effective_routes(sub_id, rg_name, vm_name)
                        
                        # If VM has network interfaces, test NIC routes endpoint
                        if vm_detail and "network_interfaces" in vm_detail and vm_detail["network_interfaces"]:
                            nic_name = vm_detail["network_interfaces"][0].get("name")
                            self.test_nic_effective_routes(sub_id, rg_name, nic_name)

            # Test VM shortcuts endpoints
            self.test_vm_shortcuts()

            # Test VM hostnames endpoint
            self.test_vm_hostnames()

            return True

        except Exception as e:
            logger.error(f"Error running tests: {e}", exc_info=True)
            return False

        finally:
            self.end_time = time.time()

            # Generate the report regardless of test outcome
            self.generate_report()

            # Stop the server if we started it
            if self.server_process:
                self.stop_server()

    def test_ping(self) -> bool:
        """Test the health check endpoint"""
        test = EndpointTest(name="Health Check", url=f"{self.api_url}/ping")
        self.test_results.append(test)

        test.start()
        try:
            response = self.session.get(test.url, timeout=self.timeout)

            # Basic validation - expecting "pong" response
            success = response.status_code == 200 and response.text.strip('"') == "pong"
            test.complete(response, success)

            if success:
                test.add_validation("Status Code", True, "Expected: 200")
                test.add_validation("Response Content", True, "Expected: pong")
                logger.info(f"✅ Successfully tested health check endpoint")
            else:
                test.add_validation(
                    "Status Code",
                    response.status_code == 200,
                    f"Expected: 200, Got: {response.status_code}",
                )
                test.add_validation(
                    "Response Content",
                    response.text.strip('"') == "pong",
                    f"Expected: pong, Got: {response.text}",
                )
                logger.error(
                    f"❌ Health check endpoint test failed: {response.status_code}"
                )

            return success

        except Exception as e:
            test.complete(None, False, str(e))
            logger.error(f"❌ Health check endpoint test error: {e}")
            return False

    def test_subscriptions(self) -> List[Dict]:
        """Test the subscriptions endpoint"""
        test = EndpointTest(
            name="List Subscriptions", url=f"{self.api_url}/subscriptions/"
        )
        self.test_results.append(test)

        test.start()
        try:
            response = self.session.get(test.url, timeout=self.timeout)

            # Parse and validate JSON response
            success = response.status_code == 200
            if success:
                data = response.json()
                # Validate response structure - expect list of subscription objects
                success = isinstance(data, list)

                # Additional validations
                if success and data:
                    # Validate first subscription has expected fields
                    sub = data[0]
                    has_expected_fields = all(
                        field in sub
                        for field in ["id", "name", "display_name", "state"]
                    )
                    test.add_validation(
                        "Has Expected Fields",
                        has_expected_fields,
                        "Subscription should have id, name, display_name, and state fields",
                    )

                    # Validate subscription ID format (UUID)
                    valid_uuid = len(sub.get("id", "").split("-")) == 5
                    test.add_validation(
                        "Valid UUID Format",
                        valid_uuid,
                        "Subscription ID should be in UUID format",
                    )

                    success = success and has_expected_fields and valid_uuid

                test.add_validation("Status Code", True, "Expected: 200")
                test.add_validation(
                    "Response Type",
                    isinstance(data, list),
                    "Expected a list of subscriptions",
                )
                test.add_validation(
                    "Found Subscriptions",
                    len(data) > 0,
                    f"Found {len(data)} subscriptions",
                )

                if success:
                    logger.info(
                        f"✅ Successfully tested subscriptions endpoint. Found {len(data)} subscriptions."
                    )
                else:
                    logger.warning(
                        f"⚠️ Subscriptions endpoint returned data but validation failed"
                    )

                test.complete(response, success)
                return data if success else []

            else:
                test.add_validation(
                    "Status Code", False, f"Expected: 200, Got: {response.status_code}"
                )
                test.complete(response, False)
                logger.error(
                    f"❌ Subscriptions endpoint test failed: {response.status_code}"
                )
                return []

        except Exception as e:
            test.complete(None, False, str(e))
            logger.error(f"❌ Subscriptions endpoint test error: {e}")
            return []

    def test_resource_groups(self, subscription_id: str) -> List[Dict]:
        """Test the resource groups endpoint"""
        test = EndpointTest(
            name="List Resource Groups",
            url=f"{self.api_url}/subscriptions/{subscription_id}/resource-groups/",
        )
        self.test_results.append(test)

        test.start()
        try:
            response = self.session.get(test.url, timeout=self.timeout)

            # Parse and validate JSON response
            success = response.status_code == 200
            if success:
                data = response.json()
                # Validate response structure - expect list of resource group objects
                success = isinstance(data, list)

                # Additional validations
                if success and data:
                    # Validate first resource group has expected fields
                    rg = data[0]
                    has_expected_fields = all(
                        field in rg for field in ["id", "name", "location"]
                    )
                    test.add_validation(
                        "Has Expected Fields",
                        has_expected_fields,
                        "Resource group should have id, name, and location fields",
                    )

                test.add_validation("Status Code", True, "Expected: 200")
                test.add_validation(
                    "Response Type",
                    isinstance(data, list),
                    "Expected a list of resource groups",
                )
                test.add_validation(
                    "Found Resource Groups",
                    len(data) > 0,
                    f"Found {len(data)} resource groups",
                )

                if success:
                    logger.info(
                        f"✅ Successfully tested resource groups endpoint. Found {len(data)} resource groups."
                    )
                else:
                    logger.warning(
                        f"⚠️ Resource groups endpoint returned data but validation failed"
                    )

                test.complete(response, success)
                return data if success else []

            else:
                test.add_validation(
                    "Status Code", False, f"Expected: 200, Got: {response.status_code}"
                )
                test.complete(response, False)
                logger.error(
                    f"❌ Resource groups endpoint test failed: {response.status_code}"
                )
                return []

        except Exception as e:
            test.complete(None, False, str(e))
            logger.error(f"❌ Resource groups endpoint test error: {e}")
            return []

    def test_virtual_machines(
        self, subscription_id: str, resource_group_name: str
    ) -> Tuple[List[Dict], Dict]:
        """Test the virtual machines endpoints"""
        # Test list VMs endpoint
        vm_list_test = EndpointTest(
            name="List Virtual Machines",
            url=f"{self.api_url}/subscriptions/{subscription_id}/resource-groups/{resource_group_name}/virtual-machines/",
        )
        self.test_results.append(vm_list_test)

        vm_details = None
        vm_list_test.start()

        try:
            response = self.session.get(vm_list_test.url, timeout=self.timeout)

            # Parse and validate JSON response
            success = response.status_code == 200
            if success:
                data = response.json()
                # Validate response structure
                success = isinstance(data, list)

                vm_list_test.add_validation("Status Code", True, "Expected: 200")
                vm_list_test.add_validation(
                    "Response Type", isinstance(data, list), "Expected a list of VMs"
                )

                if data:
                    # Validate first VM has expected fields
                    vm = data[0]
                    has_expected_fields = all(
                        field in vm
                        for field in ["id", "name", "location", "vm_size", "os_type"]
                    )
                    vm_list_test.add_validation(
                        "Has Expected Fields",
                        has_expected_fields,
                        "VM should have id, name, location, vm_size, and os_type fields",
                    )

                    vm_list_test.add_validation(
                        "Found VMs", True, f"Found {len(data)} VMs"
                    )
                    logger.info(
                        f"✅ Successfully tested VM list endpoint. Found {len(data)} VMs."
                    )

                    # Now test the VM details endpoint for the first VM
                    vm_name = vm.get("name")
                    vm_details = self.test_vm_details(
                        subscription_id, resource_group_name, vm_name
                    )
                else:
                    vm_list_test.add_validation(
                        "Found VMs", False, "No VMs found in resource group"
                    )
                    logger.warning(
                        f"⚠️ No VMs found in resource group {resource_group_name}"
                    )

                vm_list_test.complete(response, success)
                return data if success else [], vm_details

            else:
                vm_list_test.add_validation(
                    "Status Code", False, f"Expected: 200, Got: {response.status_code}"
                )
                vm_list_test.complete(response, False)
                logger.error(f"❌ VM list endpoint test failed: {response.status_code}")
                return [], None

        except Exception as e:
            vm_list_test.complete(None, False, str(e))
            logger.error(f"❌ VM list endpoint test error: {e}")
            return [], None

    def test_vm_details(
        self, subscription_id: str, resource_group_name: str, vm_name: str
    ) -> Dict:
        """Test the VM details endpoint"""
        test = EndpointTest(
            name="VM Details",
            url=f"{self.api_url}/subscriptions/{subscription_id}/resource-groups/{resource_group_name}/virtual-machines/{vm_name}",
        )
        self.test_results.append(test)

        test.start()
        try:
            response = self.session.get(test.url, timeout=self.timeout)

            # Parse and validate JSON response
            success = response.status_code == 200
            if success:
                data = response.json()

                # Validate basic fields
                has_basic_fields = all(
                    field in data
                    for field in ["id", "name", "location", "vm_size", "os_type"]
                )
                test.add_validation(
                    "Has Basic Fields",
                    has_basic_fields,
                    "VM should have id, name, location, vm_size, and os_type fields",
                )

                # Validate network interfaces
                has_network_interfaces = "network_interfaces" in data and isinstance(
                    data["network_interfaces"], list
                )
                test.add_validation(
                    "Has Network Interfaces",
                    has_network_interfaces,
                    "VM should have network_interfaces array",
                )

                # Validate NSG rules if present
                if "effective_nsg_rules" in data:
                    has_nsg_rules = isinstance(data["effective_nsg_rules"], list)
                    if has_nsg_rules and data["effective_nsg_rules"]:
                        rule = data["effective_nsg_rules"][0]
                        rule_has_fields = all(
                            field in rule
                            for field in [
                                "name",
                                "direction",
                                "protocol",
                                "port_range",
                                "access",
                            ]
                        )
                        test.add_validation(
                            "NSG Rules Format",
                            rule_has_fields,
                            "NSG rules should have expected fields",
                        )

                test.add_validation("Status Code", True, "Expected: 200")

                # Overall success
                success = has_basic_fields and has_network_interfaces

                if success:
                    logger.info(
                        f"✅ Successfully tested VM details endpoint for {vm_name}"
                    )
                else:
                    logger.warning(
                        f"⚠️ VM details endpoint returned data but validation failed for {vm_name}"
                    )

                test.complete(response, success)
                return data if success else {}

            else:
                test.add_validation(
                    "Status Code", False, f"Expected: 200, Got: {response.status_code}"
                )
                test.complete(response, False)
                logger.error(
                    f"❌ VM details endpoint test failed for {vm_name}: {response.status_code}"
                )
                return {}

        except Exception as e:
            test.complete(None, False, str(e))
            logger.error(f"❌ VM details endpoint test error for {vm_name}: {e}")
            return {}

    def test_vm_shortcuts(self) -> Tuple[List[Dict], Dict]:
        """Test the VM shortcuts endpoints"""
        # Test list all VMs endpoint
        test_list = EndpointTest(
            name="List All VMs Shortcut",
            url=f"{self.api_url}/subscriptions/virtual_machines/",
        )
        self.test_results.append(test_list)

        vm_detail = None
        test_list.start()

        try:
            response = self.session.get(test_list.url, timeout=self.timeout)

            # Parse and validate JSON response
            success = response.status_code == 200
            if success:
                data = response.json()

                # Validate response structure
                success = isinstance(data, list)

                test_list.add_validation("Status Code", True, "Expected: 200")
                test_list.add_validation(
                    "Response Type", isinstance(data, list), "Expected a list of VMs"
                )

                if data:
                    # Validate first VM has expected fields
                    vm = data[0]
                    has_expected_fields = all(
                        field in vm
                        for field in [
                            "id",
                            "name",
                            "location",
                            "vm_size",
                            "os_type",
                            "subscription_id",
                            "subscription_name",
                            "resource_group_name",
                        ]
                    )
                    test_list.add_validation(
                        "Has Expected Fields",
                        has_expected_fields,
                        "VM should have all expected fields including context data",
                    )

                    test_list.add_validation(
                        "Found VMs", True, f"Found {len(data)} VMs"
                    )
                    logger.info(
                        f"✅ Successfully tested all VMs shortcut endpoint. Found {len(data)} VMs."
                    )

                    # Now test the VM details by name endpoint for the first VM
                    vm_name = vm.get("name")
                    vm_detail = self.test_vm_by_name(vm_name)
                else:
                    test_list.add_validation("Found VMs", False, "No VMs found")
                    logger.warning(f"⚠️ No VMs found in the shortcuts endpoint")

                test_list.complete(response, success)
                return data if success else [], vm_detail

            else:
                test_list.add_validation(
                    "Status Code", False, f"Expected: 200, Got: {response.status_code}"
                )
                test_list.complete(response, False)
                logger.error(
                    f"❌ All VMs shortcut endpoint test failed: {response.status_code}"
                )
                return [], None

        except Exception as e:
            test_list.complete(None, False, str(e))
            logger.error(f"❌ All VMs shortcut endpoint test error: {e}")
            return [], None

    def test_vm_by_name(self, vm_name: str) -> Dict:
        """Test the VM by name shortcut endpoint"""
        test = EndpointTest(
            name="VM By Name Shortcut",
            url=f"{self.api_url}/subscriptions/virtual_machines/{vm_name}",
        )
        self.test_results.append(test)

        test.start()
        try:
            response = self.session.get(test.url, timeout=self.timeout)

            # Parse and validate JSON response
            success = response.status_code == 200
            if success:
                data = response.json()

                # Validate basic fields
                has_basic_fields = all(
                    field in data
                    for field in ["id", "name", "location", "vm_size", "os_type"]
                )
                test.add_validation(
                    "Has Basic Fields",
                    has_basic_fields,
                    "VM should have id, name, location, vm_size, and os_type fields",
                )

                # Validate network interfaces
                has_network_interfaces = "network_interfaces" in data and isinstance(
                    data["network_interfaces"], list
                )
                test.add_validation(
                    "Has Network Interfaces",
                    has_network_interfaces,
                    "VM should have network_interfaces array",
                )

                test.add_validation("Status Code", True, "Expected: 200")

                # Overall success
                success = has_basic_fields and has_network_interfaces

                if success:
                    logger.info(
                        f"✅ Successfully tested VM by name shortcut endpoint for {vm_name}"
                    )
                else:
                    logger.warning(
                        f"⚠️ VM by name shortcut endpoint returned data but validation failed for {vm_name}"
                    )

                test.complete(response, success)
                return data if success else {}

            else:
                test.add_validation(
                    "Status Code", False, f"Expected: 200, Got: {response.status_code}"
                )
                test.complete(response, False)
                logger.error(
                    f"❌ VM by name shortcut endpoint test failed for {vm_name}: {response.status_code}"
                )
                return {}

        except Exception as e:
            test.complete(None, False, str(e))
            logger.error(
                f"❌ VM by name shortcut endpoint test error for {vm_name}: {e}"
            )
            return {}

    def test_vm_hostnames(self) -> List[Dict]:
        """Test the VM hostnames endpoint"""
        test = EndpointTest(
            name="VM Hostnames", url=f"{self.api_url}/subscriptions/hostnames/"
        )
        self.test_results.append(test)

        test.start()
        try:
            response = self.session.get(test.url, timeout=self.timeout)

            # Parse and validate JSON response
            success = response.status_code == 200
            if success:
                data = response.json()

                # Validate response structure
                success = isinstance(data, list)

                test.add_validation("Status Code", True, "Expected: 200")
                test.add_validation(
                    "Response Type",
                    isinstance(data, list),
                    "Expected a list of VM hostnames",
                )

                if data:
                    # Validate first hostname entry has expected fields
                    entry = data[0]
                    has_expected_fields = all(
                        field in entry for field in ["vm_name", "hostname"]
                    )
                    test.add_validation(
                        "Has Expected Fields",
                        has_expected_fields,
                        "VM hostname entry should have vm_name and hostname fields",
                    )

                    test.add_validation(
                        "Found Entries", True, f"Found {len(data)} VM hostname entries"
                    )
                    logger.info(
                        f"✅ Successfully tested VM hostnames endpoint. Found {len(data)} entries."
                    )
                else:
                    test.add_validation(
                        "Found Entries", False, "No VM hostname entries found"
                    )
                    logger.warning(f"⚠️ No VM hostname entries found")

                test.complete(response, success)
                return data if success else []

            else:
                test.add_validation(
                    "Status Code", False, f"Expected: 200, Got: {response.status_code}"
                )
                test.complete(response, False)
                logger.error(
                    f"❌ VM hostnames endpoint test failed: {response.status_code}"
                )
                return []

        except Exception as e:
            test.complete(None, False, str(e))
            logger.error(f"❌ VM hostnames endpoint test error: {e}")
            return []

    def test_route_tables(self, subscription_id: str) -> List[Dict]:
        """Test the route tables endpoint"""
        test = EndpointTest(
            name="List Route Tables",
            url=f"{self.api_url}/subscriptions/{subscription_id}/routetables",
        )
        self.test_results.append(test)

        test.start()
        try:
            response = self.session.get(test.url, timeout=self.timeout)

            # Parse and validate JSON response
            success = response.status_code == 200
            if success:
                data = response.json()
                # Validate response structure - expect list of route table summary objects
                success = isinstance(data, list)

                # Additional validations
                if success and data:
                    # Validate first route table has expected fields
                    rt = data[0]
                    has_expected_fields = all(
                        field in rt for field in ["id", "name", "location", "resource_group", "route_count", "subnet_count"]
                    )
                    test.add_validation(
                        "Has Expected Fields",
                        has_expected_fields,
                        "Route table should have id, name, location, resource_group, route_count, and subnet_count fields",
                    )

                test.add_validation("Status Code", True, "Expected: 200")
                test.add_validation(
                    "Response Type",
                    isinstance(data, list),
                    "Expected a list of route tables",
                )
                test.add_validation(
                    "Found Route Tables",
                    len(data) > 0,
                    f"Found {len(data)} route tables",
                )

                if success:
                    logger.info(
                        f"✅ Successfully tested route tables endpoint. Found {len(data)} route tables."
                    )
                else:
                    logger.warning(
                        f"⚠️ Route tables endpoint returned data but validation failed"
                    )

                test.complete(response, success)
                return data if success else []

            else:
                test.add_validation(
                    "Status Code", False, f"Expected: 200, Got: {response.status_code}"
                )
                test.complete(response, False)
                logger.error(
                    f"❌ Route tables endpoint test failed: {response.status_code}"
                )
                return []

        except Exception as e:
            test.complete(None, False, str(e))
            logger.error(f"❌ Route tables endpoint test error: {e}")
            return []

    def test_route_table_details(
        self, subscription_id: str, resource_group_name: str, route_table_name: str
    ) -> Dict:
        """Test the route table details endpoint"""
        test = EndpointTest(
            name="Route Table Details",
            url=f"{self.api_url}/subscriptions/{subscription_id}/resourcegroups/{resource_group_name}/routetables/{route_table_name}",
        )
        self.test_results.append(test)

        test.start()
        try:
            response = self.session.get(test.url, timeout=self.timeout)

            # Parse and validate JSON response
            success = response.status_code == 200
            if success:
                data = response.json()

                # Validate basic fields
                has_basic_fields = all(
                    field in data
                    for field in ["id", "name", "location", "resource_group", "routes", "subnets"]
                )
                test.add_validation(
                    "Has Basic Fields",
                    has_basic_fields,
                    "Route table should have id, name, location, resource_group, routes, and subnets fields",
                )

                # Validate routes
                has_routes = "routes" in data and isinstance(
                    data["routes"], list
                )
                test.add_validation(
                    "Has Routes Array",
                    has_routes,
                    "Route table should have routes array",
                )

                # Validate route entries if present
                if has_routes and data["routes"]:
                    route = data["routes"][0]
                    route_has_fields = all(
                        field in route
                        for field in [
                            "name",
                            "address_prefix",
                            "next_hop_type",
                        ]
                    )
                    test.add_validation(
                        "Route Entry Format",
                        route_has_fields,
                        "Route entries should have expected fields",
                    )

                test.add_validation("Status Code", True, "Expected: 200")

                # Overall success
                success = has_basic_fields and has_routes

                if success:
                    logger.info(
                        f"✅ Successfully tested route table details endpoint for {route_table_name}"
                    )
                else:
                    logger.warning(
                        f"⚠️ Route table details endpoint returned data but validation failed for {route_table_name}"
                    )

                test.complete(response, success)
                return data if success else {}

            else:
                test.add_validation(
                    "Status Code", False, f"Expected: 200, Got: {response.status_code}"
                )
                test.complete(response, False)
                logger.error(
                    f"❌ Route table details endpoint test failed for {route_table_name}: {response.status_code}"
                )
                return {}

        except Exception as e:
            test.complete(None, False, str(e))
            logger.error(f"❌ Route table details endpoint test error for {route_table_name}: {e}")
            return {}

    def test_vm_effective_routes(
        self, subscription_id: str, resource_group_name: str, vm_name: str
    ) -> List[Dict]:
        """Test the VM effective routes endpoint"""
        test = EndpointTest(
            name="VM Effective Routes",
            url=f"{self.api_url}/subscriptions/{subscription_id}/resourcegroups/{resource_group_name}/virtualmachines/{vm_name}/routes",
        )
        self.test_results.append(test)

        test.start()
        try:
            response = self.session.get(test.url, timeout=self.timeout)

            # Parse and validate JSON response
            success = response.status_code == 200
            if success:
                data = response.json()

                # Validate response structure
                success = isinstance(data, list)

                test.add_validation("Status Code", True, "Expected: 200")
                test.add_validation(
                    "Response Type",
                    isinstance(data, list),
                    "Expected a list of routes",
                )

                if data:
                    # Validate first route has expected fields
                    route = data[0]
                    has_expected_fields = all(
                        field in route
                        for field in ["address_prefix", "next_hop_type"]
                    )
                    test.add_validation(
                        "Has Expected Fields",
                        has_expected_fields,
                        "Route should have address_prefix and next_hop_type fields",
                    )

                    test.add_validation(
                        "Found Routes", True, f"Found {len(data)} routes"
                    )
                    logger.info(
                        f"✅ Successfully tested VM effective routes endpoint for {vm_name}. Found {len(data)} routes."
                    )
                else:
                    test.add_validation(
                        "Found Routes", True, "No routes found, but response is valid"
                    )
                    logger.info(
                        f"✅ Successfully tested VM effective routes endpoint for {vm_name}. No routes found."
                    )

                test.complete(response, success)
                return data if success else []

            else:
                test.add_validation(
                    "Status Code", False, f"Expected: 200, Got: {response.status_code}"
                )
                test.complete(response, False)
                logger.error(
                    f"❌ VM effective routes endpoint test failed for {vm_name}: {response.status_code}"
                )
                return []

        except Exception as e:
            test.complete(None, False, str(e))
            logger.error(f"❌ VM effective routes endpoint test error for {vm_name}: {e}")
            return []

    def test_nic_effective_routes(
        self, subscription_id: str, resource_group_name: str, nic_name: str
    ) -> List[Dict]:
        """Test the NIC effective routes endpoint"""
        test = EndpointTest(
            name="NIC Effective Routes",
            url=f"{self.api_url}/subscriptions/{subscription_id}/resourcegroups/{resource_group_name}/networkinterfaces/{nic_name}/routes",
        )
        self.test_results.append(test)

        test.start()
        try:
            response = self.session.get(test.url, timeout=self.timeout)

            # Parse and validate JSON response
            success = response.status_code == 200
            if success:
                data = response.json()

                # Validate response structure
                success = isinstance(data, list)

                test.add_validation("Status Code", True, "Expected: 200")
                test.add_validation(
                    "Response Type",
                    isinstance(data, list),
                    "Expected a list of routes",
                )

                if data:
                    # Validate first route has expected fields
                    route = data[0]
                    has_expected_fields = all(
                        field in route
                        for field in ["address_prefix", "next_hop_type"]
                    )
                    test.add_validation(
                        "Has Expected Fields",
                        has_expected_fields,
                        "Route should have address_prefix and next_hop_type fields",
                    )

                    test.add_validation(
                        "Found Routes", True, f"Found {len(data)} routes"
                    )
                    logger.info(
                        f"✅ Successfully tested NIC effective routes endpoint for {nic_name}. Found {len(data)} routes."
                    )
                else:
                    test.add_validation(
                        "Found Routes", True, "No routes found, but response is valid"
                    )
                    logger.info(
                        f"✅ Successfully tested NIC effective routes endpoint for {nic_name}. No routes found."
                    )

                test.complete(response, success)
                return data if success else []

            else:
                test.add_validation(
                    "Status Code", False, f"Expected: 200, Got: {response.status_code}"
                )
                test.complete(response, False)
                logger.error(
                    f"❌ NIC effective routes endpoint test failed for {nic_name}: {response.status_code}"
                )
                return []

        except Exception as e:
            test.complete(None, False, str(e))
            logger.error(f"❌ NIC effective routes endpoint test error for {nic_name}: {e}")
            return []

    def generate_report(self):
        """Generate an HTML test report"""
        # Ensure report directory exists
        os.makedirs(REPORT_DIR, exist_ok=True)

        # Calculate summary metrics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for test in self.test_results if test.success)
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        total_duration = (
            self.end_time - self.start_time if self.end_time and self.start_time else 0
        )

        # Prepare timestamp for filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = (
            REPORT_DIR / f"integration_test_report_{timestamp}_{self.test_id}.html"
        )

        # Generate HTML report
        with open(report_file, "w") as f:
            f.write(
                f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Integration Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; color: #333; }}
        h1, h2, h3 {{ color: #444; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .summary {{ background-color: #f5f5f5; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .summary-item {{ margin-bottom: 10px; }}
        .test-results {{ margin-bottom: 30px; }}
        .test-case {{ background-color: #fff; border: 1px solid #ddd; border-radius: 5px; margin-bottom: 15px; overflow: hidden; }}
        .test-header {{ padding: 15px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; }}
        .test-details {{ padding: 15px; }}
        .validation {{ margin-bottom: 10px; padding: 10px; border-radius: 3px; }}
        .success {{ background-color: #d4edda; color: #155724; }}
        .error {{ background-color: #f8d7da; color: #721c24; }}
        .warning {{ background-color: #fff3cd; color: #856404; }}
        .info {{ background-color: #d1ecf1; color: #0c5460; }}
        .badge {{ display: inline-block; padding: 5px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; }}
        .badge-success {{ background-color: #28a745; color: white; }}
        .badge-danger {{ background-color: #dc3545; color: white; }}
        .url {{ font-family: monospace; word-break: break-all; padding: 5px; background-color: #f8f9fa; border-radius: 3px; }}
        .details-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        .details-table th, .details-table td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
        .details-table th {{ background-color: #f5f5f5; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Azure RM Proxy API Integration Test Report</h1>
        <div class="summary">
            <h2>Summary</h2>
            <div class="summary-item"><strong>Test Date:</strong> {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
            <div class="summary-item"><strong>Total Tests:</strong> {total_tests}</div>
            <div class="summary-item"><strong>Passed:</strong> {passed_tests}</div>
            <div class="summary-item"><strong>Failed:</strong> {failed_tests}</div>
            <div class="summary-item"><strong>Success Rate:</strong> {success_rate:.1f}%</div>
            <div class="summary-item"><strong>Total Duration:</strong> {total_duration:.2f} seconds</div>
            <div class="summary-item"><strong>Server:</strong> {self.host}:{self.port}</div>
            <div class="summary-item"><strong>Mock Mode:</strong> {self.use_mock}</div>
        </div>
        
        <div class="test-results">
            <h2>Test Results</h2>
"""
            )

            # Add test cases
            for test in self.test_results:
                status_class = "success" if test.success else "error"
                status_badge = (
                    f"<span class='badge badge-{'success' if test.success else 'danger'}'>"
                    + f"{'PASSED' if test.success else 'FAILED'}</span>"
                )

                f.write(
                    f"""
            <div class="test-case">
                <div class="test-header {status_class}">
                    <h3>{html.escape(test.name)}</h3>
                    {status_badge}
                </div>
                <div class="test-details">
                    <div><strong>URL:</strong> <span class="url">{html.escape(test.url)}</span></div>
                    <div><strong>Method:</strong> {test.method}</div>
                    <div><strong>Duration:</strong> {test.duration:.4f}s</div>
                    <div><strong>Status Code:</strong> {test.status_code or 'N/A'}</div>
                    
                    {f"<div class='error'><strong>Error:</strong> {html.escape(test.error)}</div>" if test.error else ""}
                    
                    <h4>Validations</h4>
"""
                )

                # Add validation results
                if test.validation_results:
                    for validation in test.validation_results:
                        validation_class = (
                            "success" if validation["success"] else "error"
                        )
                        f.write(
                            f"""
                    <div class="validation {validation_class}">
                        <strong>{html.escape(validation["name"])}:</strong> {html.escape(validation["details"])}
                    </div>
"""
                        )
                else:
                    f.write(
                        "                    <div class='info'>No validations performed</div>\n"
                    )

                f.write("                </div>\n            </div>\n")

            # Close HTML
            f.write(
                """
        </div>
    </div>
</body>
</html>
"""
            )

        logger.info(f"Test report generated: {report_file}")

        # Also write a JSON version for machine processing
        json_file = (
            REPORT_DIR / f"integration_test_report_{timestamp}_{self.test_id}.json"
        )
        with open(json_file, "w") as f:
            json.dump(
                {
                    "summary": {
                        "timestamp": datetime.datetime.now().isoformat(),
                        "total_tests": total_tests,
                        "passed_tests": passed_tests,
                        "failed_tests": failed_tests,
                        "success_rate": success_rate,
                        "total_duration": total_duration,
                        "server": f"{self.host}:{self.port}",
                        "mock_mode": self.use_mock,
                    },
                    "tests": [test.as_dict() for test in self.test_results],
                },
                f,
                indent=2,
            )

        logger.info(f"JSON test report generated: {json_file}")

        # Print summary to console
        print("\n" + "=" * 80)
        print(f"INTEGRATION TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed:      {passed_tests}")
        print(f"Failed:      {failed_tests}")
        print(f"Success:     {success_rate:.1f}%")
        print(f"Duration:    {total_duration:.2f} seconds")
        print(f"Report:      {report_file}")
        print("=" * 80 + "\n")

        return report_file, json_file


def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(
        description="Run integration tests for Azure RM Proxy Server"
    )
    parser.add_argument(
        "--mock", action="store_true", help="Use mock service instead of real Azure"
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"Host to bind server to (default: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port to bind server to (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Request timeout in seconds (default: {DEFAULT_TIMEOUT})",
    )
    parser.add_argument(
        "--no-server",
        action="store_true",
        help="Don't start the server (use if server is already running)",
    )

    args = parser.parse_args()

    # Create and run integration test
    test = APIIntegrationTest(
        host=args.host, port=args.port, use_mock=args.mock, timeout=args.timeout
    )

    # If no-server option is used, set server_process to a dummy value so tests will run without starting server
    if args.no_server:
        test.server_process = True  # This prevents test from trying to start the server

    success = test.run_tests()

    # Return appropriate exit code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
