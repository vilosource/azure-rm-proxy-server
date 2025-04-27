#!/usr/bin/env python3
"""
Smoke Test with Cache for Azure RM Proxy Server

This script performs a live smoke test of the Azure RM Proxy server by:
1. Starting the API server in a separate process (or connecting to a running instance)
2. Testing all API endpoints with real Azure data
3. Verifying caching works correctly by making repeated calls
4. Measuring performance impact of caching
5. Generating a test report

Usage:
    python -m azure_rm_proxy.tests.scripts.smoke_test_with_cache [--host HOST] [--port PORT] [--no-server] [--test TEST]
"""

# List of all possible URLs that can be reached based on the defined API patterns:
# 1. /api/subscriptions/
# 2. /api/subscriptions/{subscription_id}/resource-groups/
# 3. /api/subscriptions/{subscription_id}/resource-groups/{resource_group_name}/virtual-machines/
# 4. /api/subscriptions/{subscription_id}/resource-groups/{resource_group_name}/virtual-machines/{vm_name}
# 5. /api/subscriptions/virtual_machines/
# 6. /api/subscriptions/virtual_machines/{vm_name}
# 7. /api/subscriptions/hostnames/
# 8. /api/reports/virtual-machines
# 9. /api/subscriptions/{subscription_id}/routetables
# 10. /api/subscriptions/{subscription_id}/resourcegroups/{resource_group_name}/routetables/{route_table_name}
# 11. /api/subscriptions/{subscription_id}/resourcegroups/{resource_group_name}/virtualmachines/{vm_name}/routes
# 12. /api/subscriptions/{subscription_id}/resourcegroups/{resource_group_name}/networkinterfaces/{nic_name}/routes

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
import requests
import statistics
from typing import Dict, List, Tuple, Optional, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))


class SmokeTestRunner:
    """Runs smoke tests against the Azure RM Proxy server with caching enabled."""

    def __init__(self, host: str = "localhost", port: int = 8000, start_server: bool = True):
        """Initialize the smoke test runner.
        
        Args:
            host: Hostname of the Azure RM Proxy server
            port: Port of the Azure RM Proxy server
            start_server: Whether to start the server or use an existing instance
        """
        self.host = host
        self.port = port
        self.start_server = start_server
        self.base_url = f"http://{host}:{port}"
        self.server_process = None
        self.results = {}
        
        # Get the project root directory (where docker-compose.yml is located)
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
        
        # Create reports directory if it doesn't exist
        reports_dir = os.path.join(self.project_root, "test_reports")
        os.makedirs(reports_dir, exist_ok=True)
        
        # Set up report file name with timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.report_file = os.path.join(reports_dir, f"smoke_test_report_{timestamp}.json")

    def check_redis_running(self) -> bool:
        """Check if Redis is running, and start it if needed.
        
        Returns:
            bool: True if Redis is running or was started successfully
        """
        print("Checking if Redis is running...")
        
        # Check if Redis container is running using docker compose
        try:
            # Always run docker compose commands from the project root
            result = subprocess.run(
                ["docker", "compose", "ps", "--format", "json"], 
                capture_output=True, 
                text=True, 
                check=True,
                cwd=self.project_root  # Specify the directory where docker-compose.yml is located
            )
            
            if not result.stdout.strip():
                print("No containers running, starting Redis...")
                return self._start_redis()
            
            containers = json.loads(result.stdout)
            if isinstance(containers, dict):  # Handle single container case
                containers = [containers]
                
            redis_running = any(
                container.get("Service") == "redis" and 
                container.get("State") == "running" 
                for container in containers
            )
            
            if redis_running:
                print("Redis is already running.")
                return True
            else:
                print("Redis is not running, starting it...")
                return self._start_redis()
                
        except (subprocess.SubprocessError, json.JSONDecodeError) as e:
            print(f"Error checking Redis status: {e}")
            print("Attempting to start Redis...")
            return self._start_redis()
    
    def _start_redis(self) -> bool:
        """Start Redis using docker compose.
        
        Returns:
            bool: True if Redis was started successfully
        """
        try:
            # Start Redis container from the project root
            subprocess.run(
                ["docker", "compose", "up", "-d", "redis"],
                check=True,
                cwd=self.project_root  # Specify the directory where docker-compose.yml is located
            )
            
            # Wait for Redis to be ready
            max_attempts = 10
            for attempt in range(1, max_attempts + 1):
                print(f"Waiting for Redis to be ready (attempt {attempt}/{max_attempts})...")
                
                try:
                    result = subprocess.run(
                        ["docker", "compose", "exec", "redis", "redis-cli", "ping"],
                        capture_output=True,
                        text=True,
                        check=False,
                        cwd=self.project_root  # Specify the directory where docker-compose.yml is located
                    )
                    
                    if "PONG" in result.stdout:
                        print("Redis is ready!")
                        return True
                        
                except subprocess.SubprocessError:
                    pass
                
                time.sleep(2)
            
            print(f"Redis failed to start properly after {max_attempts} attempts.")
            print("Please check the Redis container logs: docker compose logs redis")
            return False
            
        except subprocess.SubprocessError as e:
            print(f"Error starting Redis: {e}")
            return False
    
    def start_proxy_server(self) -> bool:
        """Start the Azure RM Proxy server in a separate process with Redis caching.
        
        Returns:
            bool: True if the server was started successfully
        """
        if not self.start_server:
            print(f"Using existing Azure RM Proxy server at {self.base_url}")
            return True
            
        print("Starting Azure RM Proxy server with Redis caching...")
        
        # Set environment variables for Redis caching
        env = os.environ.copy()
        env["CACHE_TYPE"] = "redis"
        env["REDIS_URL"] = "redis://localhost:6379/0"
        env["REDIS_PREFIX"] = "azure_rm_proxy:"
        
        try:
            # Start the server using poetry from the project root
            self.server_process = subprocess.Popen(
                ["poetry", "run", "start-proxy"], 
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.project_root  # Run from project root directory
            )
            
            # Wait for server to be ready
            max_attempts = 10
            for attempt in range(1, max_attempts + 1):
                print(f"Waiting for server to be ready (attempt {attempt}/{max_attempts})...")
                try:
                    response = requests.get(f"{self.base_url}/api/ping")
                    if response.status_code == 200:
                        print("Azure RM Proxy server is ready!")
                        return True
                except requests.RequestException:
                    pass
                    
                time.sleep(2)
                
            print("Failed to start Azure RM Proxy server.")
            return False
            
        except Exception as e:
            print(f"Error starting Azure RM Proxy server: {e}")
            return False
    
    def test_subscriptions_endpoint(self) -> Dict[str, Any]:
        """Test the /api/subscriptions/ endpoint with caching.
        
        Returns:
            dict: Test results with response data and performance metrics
        """
        endpoint = "/api/subscriptions/"
        url = f"{self.base_url}{endpoint}"
        
        print(f"\nTesting endpoint: {endpoint}")
        print(f"Full URL: {url}")
        
        # First request (uncached)
        print("\n=== INITIAL REQUEST (UNCACHED) ===")
        print(f"GET {url}")
        start_time = time.time()
        try:
            response = requests.get(url)
            response.raise_for_status()
            first_response_time = time.time() - start_time
            first_response_data = response.json()
            print(f"Status: {response.status_code} {response.reason}")
            print(f"Time: {first_response_time:.3f}s")
            print(f"Response size: {len(response.content)} bytes")
            print(f"Cache headers: {response.headers.get('Cache-Control', 'None')}")
            
            # Display sample of response data
            if isinstance(first_response_data, list) and first_response_data:
                print(f"Found {len(first_response_data)} subscriptions")
                print("Sample subscription data:")
                print(json.dumps(first_response_data[0], indent=2)[:300] + "..." if len(json.dumps(first_response_data[0], indent=2)) > 300 else json.dumps(first_response_data[0], indent=2))
            
            # Basic validation of the response
            if not isinstance(first_response_data, list):
                return {
                    "success": False,
                    "error": "Expected a list of subscriptions, but got a different data type",
                    "status_code": response.status_code
                }
                
            if not first_response_data:
                print("Warning: No subscriptions returned. This might be expected in test environments.")
                
            for subscription in first_response_data:
                if not all(key in subscription for key in ["id", "name", "state"]):
                    return {
                        "success": False,
                        "error": "Subscription data missing required fields (id, name, state)",
                        "status_code": response.status_code
                    }
                    
        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, "status_code", None)
            }
        
        # Make several cached requests and measure performance
        print("\n=== CACHED REQUESTS ===")
        cached_times = []
        num_cached_requests = 3
        
        for i in range(num_cached_requests):
            print(f"\nCached request #{i+1}")
            print(f"GET {url}")
            start_time = time.time()
            try:
                response = requests.get(url)
                response.raise_for_status()
                cached_time = time.time() - start_time
                cached_times.append(cached_time)
                print(f"Status: {response.status_code} {response.reason}")
                print(f"Time: {cached_time:.3f}s")
                print(f"Response size: {len(response.content)} bytes")
                print(f"Cache headers: {response.headers.get('Cache-Control', 'None')}")
                
                # Verify that the cached response matches the original
                cached_data = response.json()
                if cached_data != first_response_data:
                    return {
                        "success": False,
                        "error": "Cached response data does not match the original response",
                        "status_code": response.status_code
                    }
                    
            except requests.RequestException as e:
                return {
                    "success": False, 
                    "error": f"Error during cached request {i+1}: {str(e)}",
                    "status_code": getattr(e.response, "status_code", None)
                }
        
        # Calculate performance metrics
        avg_cached_time = statistics.mean(cached_times)
        speedup_factor = first_response_time / avg_cached_time if avg_cached_time > 0 else 0
        
        print("\n=== PERFORMANCE SUMMARY ===")
        print(f"Initial request time: {first_response_time:.3f}s")
        print(f"Average cached request time: {avg_cached_time:.3f}s")
        print(f"Performance improvement with caching: {speedup_factor:.2f}x faster")
        
        return {
            "success": True,
            "endpoint": endpoint,
            "first_request_time": first_response_time,
            "cached_request_times": cached_times,
            "average_cached_time": avg_cached_time,
            "speedup_factor": speedup_factor,
            "num_subscriptions": len(first_response_data),
            "data": first_response_data,
            "status_code": response.status_code
        }
    
    def test_resource_groups_endpoint(self) -> Dict[str, Any]:
        """Test the /api/subscriptions/{subscription_id}/resource-groups/ endpoint."""
        subscriptions_endpoint = "/api/subscriptions/"
        resource_groups_endpoint_template = "/api/subscriptions/{subscription_id}/resource-groups/"

        print(f"\nTesting endpoint: {subscriptions_endpoint}")
        subscriptions_url = f"{self.base_url}{subscriptions_endpoint}"

        # Fetch subscriptions
        try:
            subscriptions_response = requests.get(subscriptions_url)
            subscriptions_response.raise_for_status()
            subscriptions = subscriptions_response.json()

            if not isinstance(subscriptions, list) or not subscriptions:
                return {
                    "success": False,
                    "error": "No subscriptions found or invalid response format",
                    "status_code": subscriptions_response.status_code
                }

        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, "status_code", None)
            }

        # Fetch resource groups for each subscription
        results = []
        for subscription in subscriptions:
            subscription_id = subscription.get("id")
            if not subscription_id:
                continue

            resource_groups_url = f"{self.base_url}{resource_groups_endpoint_template.format(subscription_id=subscription_id)}"
            print(f"\nTesting endpoint: {resource_groups_url}")

            try:
                resource_groups_response = requests.get(resource_groups_url)
                resource_groups_response.raise_for_status()
                resource_groups = resource_groups_response.json()

                if not isinstance(resource_groups, list):
                    results.append({
                        "subscription_id": subscription_id,
                        "success": False,
                        "error": "Invalid response format for resource groups",
                        "status_code": resource_groups_response.status_code
                    })
                    continue

                results.append({
                    "subscription_id": subscription_id,
                    "success": True,
                    "num_resource_groups": len(resource_groups),
                    "status_code": resource_groups_response.status_code
                })

            except requests.RequestException as e:
                results.append({
                    "subscription_id": subscription_id,
                    "success": False,
                    "error": str(e),
                    "status_code": getattr(e.response, "status_code", None)
                })

        return {
            "success": all(result["success"] for result in results),
            "details": results
        }

    def test_virtual_machines_endpoint(self) -> Dict[str, Any]:
        """Test the /api/subscriptions/{subscription_id}/resource-groups/{resource_group_name}/virtual-machines/ endpoint."""
        subscriptions_endpoint = "/api/subscriptions/"
        resource_groups_endpoint_template = "/api/subscriptions/{subscription_id}/resource-groups/"
        virtual_machines_endpoint_template = "/api/subscriptions/{subscription_id}/resource-groups/{resource_group_name}/virtual-machines/"

        print(f"\nTesting endpoint: {subscriptions_endpoint}")
        subscriptions_url = f"{self.base_url}{subscriptions_endpoint}"

        # Fetch subscriptions
        try:
            subscriptions_response = requests.get(subscriptions_url)
            subscriptions_response.raise_for_status()
            subscriptions = subscriptions_response.json()

            if not isinstance(subscriptions, list) or not subscriptions:
                return {
                    "success": False,
                    "error": "No subscriptions found or invalid response format",
                    "status_code": subscriptions_response.status_code
                }

            # Use the first subscription_id
            subscription_id = subscriptions[0].get("id")
            if not subscription_id:
                return {
                    "success": False,
                    "error": "No valid subscription ID found",
                    "status_code": subscriptions_response.status_code
                }

        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, "status_code", None)
            }

        # Fetch resource groups for the subscription
        resource_groups_url = f"{self.base_url}{resource_groups_endpoint_template.format(subscription_id=subscription_id)}"
        print(f"\nTesting endpoint: {resource_groups_url}")

        try:
            resource_groups_response = requests.get(resource_groups_url)
            resource_groups_response.raise_for_status()
            resource_groups = resource_groups_response.json()

            if not isinstance(resource_groups, list) or not resource_groups:
                return {
                    "success": False,
                    "error": "No resource groups found or invalid response format",
                    "status_code": resource_groups_response.status_code
                }

        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, "status_code", None)
            }

        # Fetch virtual machines for each resource group
        results = []
        for resource_group in resource_groups:
            resource_group_name = resource_group.get("name")
            if not resource_group_name:
                continue

            virtual_machines_url = f"{self.base_url}{virtual_machines_endpoint_template.format(subscription_id=subscription_id, resource_group_name=resource_group_name)}"
            print(f"\nTesting endpoint: {virtual_machines_url}")

            try:
                virtual_machines_response = requests.get(virtual_machines_url)
                virtual_machines_response.raise_for_status()
                virtual_machines = virtual_machines_response.json()

                if not isinstance(virtual_machines, list):
                    results.append({
                        "resource_group_name": resource_group_name,
                        "success": False,
                        "error": "Invalid response format for virtual machines",
                        "status_code": virtual_machines_response.status_code
                    })
                    continue

                results.append({
                    "resource_group_name": resource_group_name,
                    "success": True,
                    "num_virtual_machines": len(virtual_machines),
                    "status_code": virtual_machines_response.status_code
                })

            except requests.RequestException as e:
                results.append({
                    "resource_group_name": resource_group_name,
                    "success": False,
                    "error": str(e),
                    "status_code": getattr(e.response, "status_code", None)
                })

        return {
            "success": all(result["success"] for result in results),
            "details": results
        }

    def test_virtual_machine_details_endpoint(self) -> Dict[str, Any]:
        """Test the /api/subscriptions/{subscription_id}/resource-groups/{resource_group_name}/virtual-machines/{vm_name} endpoint."""
        subscriptions_endpoint = "/api/subscriptions/"
        resource_groups_endpoint_template = "/api/subscriptions/{subscription_id}/resource-groups/"
        virtual_machines_endpoint_template = "/api/subscriptions/{subscription_id}/resource-groups/{resource_group_name}/virtual-machines/"
        vm_details_endpoint_template = "/api/subscriptions/{subscription_id}/resource-groups/{resource_group_name}/virtual-machines/{vm_name}"

        print(f"\nTesting endpoint: {subscriptions_endpoint}")
        subscriptions_url = f"{self.base_url}{subscriptions_endpoint}"

        # Fetch subscriptions
        try:
            subscriptions_response = requests.get(subscriptions_url)
            subscriptions_response.raise_for_status()
            subscriptions = subscriptions_response.json()

            if not isinstance(subscriptions, list) or not subscriptions:
                return {
                    "success": False,
                    "error": "No subscriptions found or invalid response format",
                    "status_code": subscriptions_response.status_code
                }

            # Use the first subscription_id
            subscription_id = subscriptions[0].get("id")
            if not subscription_id:
                return {
                    "success": False,
                    "error": "No valid subscription ID found",
                    "status_code": subscriptions_response.status_code
                }

        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, "status_code", None)
            }

        # Fetch resource groups for the subscription
        resource_groups_url = f"{self.base_url}{resource_groups_endpoint_template.format(subscription_id=subscription_id)}"
        print(f"\nTesting endpoint: {resource_groups_url}")

        try:
            resource_groups_response = requests.get(resource_groups_url)
            resource_groups_response.raise_for_status()
            resource_groups = resource_groups_response.json()

            if not isinstance(resource_groups, list) or not resource_groups:
                return {
                    "success": False,
                    "error": "No resource groups found or invalid response format",
                    "status_code": resource_groups_response.status_code
                }

        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, "status_code", None)
            }

        # Fetch virtual machines for each resource group
        results = []
        for resource_group in resource_groups:
            resource_group_name = resource_group.get("name")
            if not resource_group_name:
                continue

            virtual_machines_url = f"{self.base_url}{virtual_machines_endpoint_template.format(subscription_id=subscription_id, resource_group_name=resource_group_name)}"
            print(f"\nTesting endpoint: {virtual_machines_url}")

            try:
                virtual_machines_response = requests.get(virtual_machines_url)
                virtual_machines_response.raise_for_status()
                virtual_machines = virtual_machines_response.json()

                if not isinstance(virtual_machines, list):
                    results.append({
                        "resource_group_name": resource_group_name,
                        "success": False,
                        "error": "Invalid response format for virtual machines",
                        "status_code": virtual_machines_response.status_code
                    })
                    continue

                # Handle case where no virtual machines are found
                if not virtual_machines:
                    results.append({
                        "resource_group_name": resource_group_name,
                        "success": True,
                        "num_virtual_machines": 0,
                        "status_code": virtual_machines_response.status_code
                    })
                    continue

                # Fetch details for each virtual machine
                for vm in virtual_machines:
                    vm_name = vm.get("name")
                    if not vm_name:
                        continue

                    vm_details_url = f"{self.base_url}{vm_details_endpoint_template.format(subscription_id=subscription_id, resource_group_name=resource_group_name, vm_name=vm_name)}"
                    print(f"\nTesting endpoint: {vm_details_url}")

                    try:
                        vm_details_response = requests.get(vm_details_url)
                        vm_details_response.raise_for_status()
                        vm_details = vm_details_response.json()

                        results.append({
                            "resource_group_name": resource_group_name,
                            "vm_name": vm_name,
                            "success": True,
                            "vm_details": vm_details,
                            "status_code": vm_details_response.status_code
                        })

                    except requests.RequestException as e:
                        results.append({
                            "resource_group_name": resource_group_name,
                            "vm_name": vm_name,
                            "success": False,
                            "error": str(e),
                            "status_code": getattr(e.response, "status_code", None)
                        })

            except requests.RequestException as e:
                results.append({
                    "resource_group_name": resource_group_name,
                    "success": False,
                    "error": str(e),
                    "status_code": getattr(e.response, "status_code", None)
                })

        return {
            "success": all(result["success"] for result in results),
            "details": results
        }

    def test_all_virtual_machines_endpoint(self) -> Dict[str, Any]:
        """Test the /api/subscriptions/virtual_machines/ endpoint."""
        all_virtual_machines_endpoint = "/api/subscriptions/virtual_machines/"

        print(f"\nTesting endpoint: {all_virtual_machines_endpoint}")
        all_virtual_machines_url = f"{self.base_url}{all_virtual_machines_endpoint}"

        # Fetch all virtual machines
        try:
            response = requests.get(all_virtual_machines_url)
            response.raise_for_status()
            virtual_machines = response.json()

            if not isinstance(virtual_machines, list):
                return {
                    "success": False,
                    "error": "Invalid response format for virtual machines",
                    "status_code": response.status_code
                }

            return {
                "success": True,
                "num_virtual_machines": len(virtual_machines),
                "status_code": response.status_code
            }

        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, "status_code", None)
            }

    def test_single_virtual_machine_endpoint(self) -> Dict[str, Any]:
        """Test the /api/subscriptions/virtual_machines/{vm_name} endpoint."""
        subscriptions_endpoint = "/api/subscriptions/"
        resource_groups_endpoint_template = "/api/subscriptions/{subscription_id}/resource-groups/"
        virtual_machines_endpoint_template = "/api/subscriptions/{subscription_id}/resource-groups/{resource_group_name}/virtual-machines/"
        single_vm_endpoint_template = "/api/subscriptions/virtual_machines/{vm_name}"

        print(f"\nTesting endpoint: {subscriptions_endpoint}")
        subscriptions_url = f"{self.base_url}{subscriptions_endpoint}"

        # Fetch subscriptions
        try:
            subscriptions_response = requests.get(subscriptions_url)
            subscriptions_response.raise_for_status()
            subscriptions = subscriptions_response.json()

            if not isinstance(subscriptions, list) or not subscriptions:
                return {
                    "success": False,
                    "error": "No subscriptions found or invalid response format",
                    "status_code": subscriptions_response.status_code
                }

        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, "status_code", None)
            }

        # Loop through subscriptions
        results = []
        for subscription in subscriptions:
            subscription_id = subscription.get("id")
            if not subscription_id:
                continue

            resource_groups_url = f"{self.base_url}{resource_groups_endpoint_template.format(subscription_id=subscription_id)}"
            print(f"\nTesting endpoint: {resource_groups_url}")

            try:
                resource_groups_response = requests.get(resource_groups_url)
                resource_groups_response.raise_for_status()
                resource_groups = resource_groups_response.json()

                if not isinstance(resource_groups, list) or not resource_groups:
                    continue

                # Choose up to 3 resource groups
                chosen_resource_groups = resource_groups[:3]

                for resource_group in chosen_resource_groups:
                    resource_group_name = resource_group.get("name")
                    if not resource_group_name:
                        continue

                    virtual_machines_url = f"{self.base_url}{virtual_machines_endpoint_template.format(subscription_id=subscription_id, resource_group_name=resource_group_name)}"
                    print(f"\nTesting endpoint: {virtual_machines_url}")

                    try:
                        virtual_machines_response = requests.get(virtual_machines_url)
                        virtual_machines_response.raise_for_status()
                        virtual_machines = virtual_machines_response.json()

                        if not isinstance(virtual_machines, list) or not virtual_machines:
                            continue

                        # Choose the first virtual machine
                        vm = virtual_machines[0]
                        vm_name = vm.get("name")
                        if not vm_name:
                            continue

                        single_vm_url = f"{self.base_url}{single_vm_endpoint_template.format(vm_name=vm_name)}"
                        print(f"\nTesting endpoint: {single_vm_url}")

                        try:
                            single_vm_response = requests.get(single_vm_url)
                            single_vm_response.raise_for_status()
                            vm_details = single_vm_response.json()

                            results.append({
                                "vm_name": vm_name,
                                "success": True,
                                "vm_details": vm_details,
                                "status_code": single_vm_response.status_code
                            })

                        except requests.RequestException as e:
                            results.append({
                                "vm_name": vm_name,
                                "success": False,
                                "error": str(e),
                                "status_code": getattr(e.response, "status_code", None)
                            })

                    except requests.RequestException as e:
                        results.append({
                            "resource_group_name": resource_group_name,
                            "success": False,
                            "error": str(e),
                            "status_code": getattr(e.response, "status_code", None)
                        })

            except requests.RequestException as e:
                results.append({
                    "subscription_id": subscription_id,
                    "success": False,
                    "error": str(e),
                    "status_code": getattr(e.response, "status_code", None)
                })

        return {
            "success": all(result["success"] for result in results),
            "details": results
        }

    def test_hostnames_endpoint(self) -> Dict[str, Any]:
        """Test the /api/subscriptions/hostnames/ endpoint."""
        hostnames_endpoint = "/api/subscriptions/hostnames/"

        print(f"\nTesting endpoint: {hostnames_endpoint}")
        hostnames_url = f"{self.base_url}{hostnames_endpoint}"

        # Fetch hostnames
        try:
            response = requests.get(hostnames_url)
            response.raise_for_status()
            hostnames = response.json()

            if not isinstance(hostnames, list):
                return {
                    "success": False,
                    "error": "Invalid response format for hostnames",
                    "status_code": response.status_code
                }

            return {
                "success": True,
                "num_hostnames": len(hostnames),
                "status_code": response.status_code
            }

        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, "status_code", None)
            }

    def test_virtual_machines_report_endpoint(self) -> Dict[str, Any]:
        """Test the /api/reports/virtual-machines endpoint."""
        virtual_machines_report_endpoint = "/api/reports/virtual-machines"

        print(f"\nTesting endpoint: {virtual_machines_report_endpoint}")
        virtual_machines_report_url = f"{self.base_url}{virtual_machines_report_endpoint}"

        # Fetch virtual machines report
        try:
            response = requests.get(virtual_machines_report_url)
            response.raise_for_status()
            report_data = response.json()

            if not isinstance(report_data, dict):
                return {
                    "success": False,
                    "error": "Invalid response format for virtual machines report",
                    "status_code": response.status_code
                }

            return {
                "success": True,
                "report_data": report_data,
                "status_code": response.status_code
            }

        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, "status_code", None)
            }

    def test_route_tables_endpoint(self) -> Dict[str, Any]:
        """Test the /api/subscriptions/{subscription_id}/routetables endpoint."""
        subscriptions_endpoint = "/api/subscriptions/"
        route_tables_endpoint_template = "/api/subscriptions/{subscription_id}/routetables"

        print(f"\nTesting endpoint: {subscriptions_endpoint}")
        subscriptions_url = f"{self.base_url}{subscriptions_endpoint}"

        # Fetch subscriptions
        try:
            subscriptions_response = requests.get(subscriptions_url)
            subscriptions_response.raise_for_status()
            subscriptions = subscriptions_response.json()

            if not isinstance(subscriptions, list) or not subscriptions:
                return {
                    "success": False,
                    "error": "No subscriptions found or invalid response format",
                    "status_code": subscriptions_response.status_code
                }

        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, "status_code", None)
            }

        # Fetch route tables for each subscription
        results = []
        for subscription in subscriptions:
            subscription_id = subscription.get("id")
            if not subscription_id:
                continue

            route_tables_url = f"{self.base_url}{route_tables_endpoint_template.format(subscription_id=subscription_id)}"
            print(f"\nTesting endpoint: {route_tables_url}")

            try:
                route_tables_response = requests.get(route_tables_url)
                route_tables_response.raise_for_status()
                route_tables = route_tables_response.json()

                if not isinstance(route_tables, list):
                    results.append({
                        "subscription_id": subscription_id,
                        "success": False,
                        "error": "Invalid response format for route tables",
                        "status_code": route_tables_response.status_code
                    })
                    continue

                results.append({
                    "subscription_id": subscription_id,
                    "success": True,
                    "num_route_tables": len(route_tables),
                    "status_code": route_tables_response.status_code
                })

            except requests.RequestException as e:
                results.append({
                    "subscription_id": subscription_id,
                    "success": False,
                    "error": str(e),
                    "status_code": getattr(e.response, "status_code", None)
                })

        return {
            "success": all(result["success"] for result in results),
            "details": results
        }

    def test_route_table_details_endpoint(self) -> Dict[str, Any]:
        """Test the /api/subscriptions/{subscription_id}/resourcegroups/{resource_group_name}/routetables/{route_table_name} endpoint."""
        subscriptions_endpoint = "/api/subscriptions/"
        route_tables_endpoint_template = "/api/subscriptions/{subscription_id}/routetables"
        route_table_details_endpoint_template = "/api/subscriptions/{subscription_id}/resourcegroups/{resource_group_name}/routetables/{route_table_name}"

        print(f"\nTesting endpoint: {subscriptions_endpoint}")
        subscriptions_url = f"{self.base_url}{subscriptions_endpoint}"

        # Fetch subscriptions
        try:
            subscriptions_response = requests.get(subscriptions_url)
            subscriptions_response.raise_for_status()
            subscriptions = subscriptions_response.json()

            if not isinstance(subscriptions, list) or not subscriptions:
                return {
                    "success": False,
                    "error": "No subscriptions found or invalid response format",
                    "status_code": subscriptions_response.status_code
                }

        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, "status_code", None)
            }

        # Fetch route tables for each subscription
        results = []
        for subscription in subscriptions:
            subscription_id = subscription.get("id")
            if not subscription_id:
                continue

            route_tables_url = f"{self.base_url}{route_tables_endpoint_template.format(subscription_id=subscription_id)}"
            print(f"\nTesting endpoint: {route_tables_url}")

            try:
                route_tables_response = requests.get(route_tables_url)
                route_tables_response.raise_for_status()
                route_tables = route_tables_response.json()

                if not isinstance(route_tables, list) or not route_tables:
                    continue

                for route_table in route_tables:
                    route_table_name = route_table.get("name")
                    resource_group_name = route_table.get("resourceGroup")
                    if not route_table_name or not resource_group_name:
                        continue

                    route_table_details_url = f"{self.base_url}{route_table_details_endpoint_template.format(subscription_id=subscription_id, resource_group_name=resource_group_name, route_table_name=route_table_name)}"
                    print(f"\nTesting endpoint: {route_table_details_url}")

                    try:
                        route_table_details_response = requests.get(route_table_details_url)
                        route_table_details_response.raise_for_status()
                        route_table_details = route_table_details_response.json()

                        results.append({
                            "subscription_id": subscription_id,
                            "resource_group_name": resource_group_name,
                            "route_table_name": route_table_name,
                            "success": True,
                            "route_table_details": route_table_details,
                            "status_code": route_table_details_response.status_code
                        })

                    except requests.RequestException as e:
                        results.append({
                            "subscription_id": subscription_id,
                            "resource_group_name": resource_group_name,
                            "route_table_name": route_table_name,
                            "success": False,
                            "error": str(e),
                            "status_code": getattr(e.response, "status_code", None)
                        })

            except requests.RequestException as e:
                results.append({
                    "subscription_id": subscription_id,
                    "success": False,
                    "error": str(e),
                    "status_code": getattr(e.response, "status_code", None)
                })

        return {
            "success": all(result["success"] for result in results),
            "details": results
        }

    def test_vm_routes_endpoint(self) -> Dict[str, Any]:
        """Test the /api/subscriptions/{subscription_id}/resourcegroups/{resource_group_name}/virtualmachines/{vm_name}/routes endpoint."""
        subscriptions_endpoint = "/api/subscriptions/"
        resource_groups_endpoint_template = "/api/subscriptions/{subscription_id}/resource-groups/"
        virtual_machines_endpoint_template = "/api/subscriptions/{subscription_id}/resource-groups/{resource_group_name}/virtual-machines/"
        vm_routes_endpoint_template = "/api/subscriptions/{subscription_id}/resourcegroups/{resource_group_name}/virtualmachines/{vm_name}/routes"

        print(f"\nTesting endpoint: {subscriptions_endpoint}")
        subscriptions_url = f"{self.base_url}{subscriptions_endpoint}"

        # Fetch subscriptions
        try:
            subscriptions_response = requests.get(subscriptions_url)
            subscriptions_response.raise_for_status()
            subscriptions = subscriptions_response.json()

            if not isinstance(subscriptions, list) or not subscriptions:
                return {
                    "success": False,
                    "error": "No subscriptions found or invalid response format",
                    "status_code": subscriptions_response.status_code
                }

        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, "status_code", None)
            }

        # Fetch resource groups and virtual machines for each subscription
        results = []
        for subscription in subscriptions:
            subscription_id = subscription.get("id")
            if not subscription_id:
                continue

            resource_groups_url = f"{self.base_url}{resource_groups_endpoint_template.format(subscription_id=subscription_id)}"
            print(f"\nTesting endpoint: {resource_groups_url}")

            try:
                resource_groups_response = requests.get(resource_groups_url)
                resource_groups_response.raise_for_status()
                resource_groups = resource_groups_response.json()

                if not isinstance(resource_groups, list) or not resource_groups:
                    continue

                for resource_group in resource_groups:
                    resource_group_name = resource_group.get("name")
                    if not resource_group_name:
                        continue

                    virtual_machines_url = f"{self.base_url}{virtual_machines_endpoint_template.format(subscription_id=subscription_id, resource_group_name=resource_group_name)}"
                    print(f"\nTesting endpoint: {virtual_machines_url}")

                    try:
                        virtual_machines_response = requests.get(virtual_machines_url)
                        virtual_machines_response.raise_for_status()
                        virtual_machines = virtual_machines_response.json()

                        if not isinstance(virtual_machines, list) or not virtual_machines:
                            continue

                        for vm in virtual_machines:
                            vm_name = vm.get("name")
                            if not vm_name:
                                continue

                            vm_routes_url = f"{self.base_url}{vm_routes_endpoint_template.format(subscription_id=subscription_id, resource_group_name=resource_group_name, vm_name=vm_name)}"
                            print(f"\nTesting endpoint: {vm_routes_url}")

                            try:
                                vm_routes_response = requests.get(vm_routes_url)
                                vm_routes_response.raise_for_status()
                                vm_routes = vm_routes_response.json()

                                results.append({
                                    "subscription_id": subscription_id,
                                    "resource_group_name": resource_group_name,
                                    "vm_name": vm_name,
                                    "success": True,
                                    "vm_routes": vm_routes,
                                    "status_code": vm_routes_response.status_code
                                })

                            except requests.RequestException as e:
                                results.append({
                                    "subscription_id": subscription_id,
                                    "resource_group_name": resource_group_name,
                                    "vm_name": vm_name,
                                    "success": False,
                                    "error": str(e),
                                    "status_code": getattr(e.response, "status_code", None)
                                })

                    except requests.RequestException as e:
                        results.append({
                            "subscription_id": subscription_id,
                            "resource_group_name": resource_group_name,
                            "success": False,
                            "error": str(e),
                            "status_code": getattr(e.response, "status_code", None)
                        })

            except requests.RequestException as e:
                results.append({
                    "subscription_id": subscription_id,
                    "success": False,
                    "error": str(e),
                    "status_code": getattr(e.response, "status_code", None)
                })

        return {
            "success": all(result["success"] for result in results),
            "details": results
        }

    def run_test_by_name(self, test_name: str) -> Optional[Dict[str, Any]]:
        """Run a specific test by its name.

        Args:
            test_name (str): The name of the test to run.

        Returns:
            Optional[Dict[str, Any]]: The result of the test, or None if the test name is invalid.
        """
        test_mapping = {
            "subscriptions": self.test_subscriptions_endpoint,
            "resource_groups": self.test_resource_groups_endpoint,
            "virtual_machines": self.test_virtual_machines_endpoint,
            "vm_details": self.test_virtual_machine_details_endpoint,
            "all_virtual_machines": self.test_all_virtual_machines_endpoint,
            "single_virtual_machine": self.test_single_virtual_machine_endpoint,
            "hostnames": self.test_hostnames_endpoint,
            "virtual_machines_report": self.test_virtual_machines_report_endpoint,
            "route_tables": self.test_route_tables_endpoint,
            "route_table_details": self.test_route_table_details_endpoint,
            "vm_routes": self.test_vm_routes_endpoint,
        }

        test_function = test_mapping.get(test_name)
        if not test_function:
            print(f"Invalid test name: {test_name}. Available tests: {', '.join(test_mapping.keys())}")
            return None

        print(f"Running test: {test_name}")
        return test_function()

    def run_all_tests(self) -> bool:
        """Run all smoke tests.
        
        Returns:
            bool: True if all tests passed
        """
        print("\n" + "="*80)
        print(f"AZURE RM PROXY SERVER SMOKE TEST WITH CACHING")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Server: {self.host}:{self.port}")
        print("="*80)
        
        # Check and start Redis if needed
        print("\n=== REDIS SETUP ===")
        if not self.check_redis_running():
            print("Failed to ensure Redis is running. Exiting.")
            return False
            
        # Start the Azure RM Proxy server if needed
        print("\n=== SERVER SETUP ===")
        if not self.start_proxy_server():
            print("Failed to ensure Azure RM Proxy server is running. Exiting.")
            return False
            
        # Run the tests
        print("\n=== RUNNING SMOKE TESTS ===")
        
        # Test /api/subscriptions endpoint
        subscription_results = self.test_subscriptions_endpoint()
        self.results["subscriptions"] = subscription_results

        # Test /api/subscriptions/{subscription_id}/resource-groups/ endpoint
        resource_groups_results = self.test_resource_groups_endpoint()
        self.results["resource_groups"] = resource_groups_results

        # Test /api/subscriptions/{subscription_id}/resource-groups/{resource_group_name}/virtual-machines/ endpoint
        virtual_machines_results = self.test_virtual_machines_endpoint()
        self.results["virtual_machines"] = virtual_machines_results

        # Test /api/subscriptions/{subscription_id}/resource-groups/{resource_group_name}/virtual-machines/{vm_name} endpoint
        vm_details_results = self.test_virtual_machine_details_endpoint()
        self.results["vm_details"] = vm_details_results

        # Test /api/subscriptions/virtual-machines/ endpoint
        all_virtual_machines_results = self.test_all_virtual_machines_endpoint()
        self.results["all_virtual_machines"] = all_virtual_machines_results

        # Test /api/subscriptions/virtual_machines/{vm_name} endpoint
        single_vm_results = self.test_single_virtual_machine_endpoint()
        self.results["single_virtual_machine"] = single_vm_results

        # Test /api/subscriptions/hostnames/ endpoint
        hostnames_results = self.test_hostnames_endpoint()
        self.results["hostnames"] = hostnames_results

        # Test /api/reports/virtual-machines endpoint
        virtual_machines_report_results = self.test_virtual_machines_report_endpoint()
        self.results["virtual_machines_report"] = virtual_machines_report_results

        # Test /api/subscriptions/{subscription_id}/routetables endpoint
        route_tables_results = self.test_route_tables_endpoint()
        self.results["route_tables"] = route_tables_results

        # Test /api/subscriptions/{subscription_id}/resourcegroups/{resource_group_name}/routetables/{route_table_name} endpoint
        route_table_details_results = self.test_route_table_details_endpoint()
        self.results["route_table_details"] = route_table_details_results

        # Test /api/subscriptions/{subscription_id}/resourcegroups/{resource_group_name}/virtualmachines/{vm_name}/routes endpoint
        vm_routes_results = self.test_vm_routes_endpoint()
        self.results["vm_routes"] = vm_routes_results
        
        # Generate report
        self.generate_report()
        
        # Determine if all tests passed
        all_passed = all(result.get("success", False) for result in self.results.values())
        
        print("\n" + "="*80)
        print("SMOKE TEST SUMMARY")
        print("="*80)
        
        for endpoint, result in self.results.items():
            status = "✅ PASSED" if result.get("success") else "❌ FAILED"
            print(f"{status} - {endpoint}")
            
            if result.get("success"):
                # Print performance data for successful tests
                print(f"  Initial request: {result.get('first_request_time', 0):.3f}s")
                print(f"  Cached requests: {result.get('average_cached_time', 0):.3f}s")
                print(f"  Speedup factor: {result.get('speedup_factor', 0):.2f}x faster with caching")
            else:
                # Print error for failed tests
                print(f"  Error: {result.get('error', 'Unknown error')}")
        
        print("\n" + "-"*80)
        if all_passed:
            print("✅ All smoke tests passed!")
        else:
            print("❌ Some smoke tests failed. See report for details.")
            
        return all_passed
    
    def generate_report(self):
        """Generate a JSON report of the test results."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "host": self.host,
            "port": self.port,
            "results": self.results
        }
        
        with open(self.report_file, "w") as f:
            json.dump(report, f, indent=2)
            
        print(f"\nTest report saved to {self.report_file}")
    
    def cleanup(self):
        """Clean up resources after tests."""
        if self.server_process:
            print("Terminating Azure RM Proxy server...")
            self.server_process.terminate()
            self.server_process.wait()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run smoke tests against Azure RM Proxy server with caching")
    parser.add_argument("--host", default="localhost", help="Hostname of the Azure RM Proxy server")
    parser.add_argument("--port", type=int, default=8000, help="Port of the Azure RM Proxy server")
    parser.add_argument("--no-server", action="store_true", help="Don't start the server, connect to running instance")
    parser.add_argument("--test", help="Run a specific test by name (e.g., subscriptions, resource_groups, etc.)")
    
    args = parser.parse_args()
    
    runner = SmokeTestRunner(
        host=args.host,
        port=args.port,
        start_server=not args.no_server
    )
    
    try:
        if args.test:
            result = runner.run_test_by_name(args.test)
            if result is None or not result.get("success", False):
                sys.exit(1)
        else:
            success = runner.run_all_tests()
            sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nSmoke tests interrupted.")
        sys.exit(1)
    finally:
        runner.cleanup()


if __name__ == "__main__":
    main()
