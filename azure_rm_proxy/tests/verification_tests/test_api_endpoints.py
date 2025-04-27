"""
List of URL patterns extracted from the OpenAPI specification:

- /api/subscriptions/  # List Subscriptions
- /api/subscriptions/{subscription_id}/resource-groups/  # List Resource Groups
- /api/subscriptions/{subscription_id}/resource-groups/{resource_group_name}/virtual-machines/  # List Virtual Machines
- /api/subscriptions/{subscription_id}/resource-groups/{resource_group_name}/virtual-machines/{vm_name}  # Get Virtual Machine Details
- /api/subscriptions/virtual_machines/  # List All Virtual Machines
- /api/subscriptions/virtual_machines/{vm_name}  # Get VM By Name
- /api/subscriptions/hostnames/  # List VM Hostnames
- /api/reports/virtual-machines  # Get VM Report
- /api/subscriptions/{subscription_id}/routetables  # List Route Tables
- /api/subscriptions/{subscription_id}/resourcegroups/{resource_group_name}/routetables/{route_table_name}  # Get Route Table Details
- /api/subscriptions/{subscription_id}/resourcegroups/{resource_group_name}/virtualmachines/{vm_name}/routes  # Get VM Effective Routes
- /api/subscriptions/{subscription_id}/resourcegroups/{resource_group_name}/networkinterfaces/{nic_name}/routes  # Get NIC Effective Routes
- /  # Get Project Info
- /api/ping  # Ping

"""

import os
import time
import requests
import subprocess
import pytest
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@pytest.fixture(autouse=True)
def enable_logging():
    logging.getLogger().setLevel(logging.INFO)

# Ensure Redis is running
def ensure_redis_running():
    logger.info("Checking if Redis is running...")
    result = subprocess.run(["docker", "compose", "ls"], capture_output=True, text=True, timeout=30)
    if "azure-rm-proxy-server" not in result.stdout or "running" not in result.stdout:
        logger.info("Redis is not running. Starting Redis...")
        subprocess.run(["docker", "compose", "up", "-d"], check=True, timeout=60)
        logger.info("Redis started successfully.")
    else:
        logger.info("Redis is already running.")

# Ensure the server is running
def ensure_server_running():
    logger.info("Checking if the server is running...")
    for attempt in range(5):
        try:
            response = requests.get("http://localhost:8000/api/ping", timeout=10)
            if response.status_code == 200:
                logger.info("Server is already running.")
                return
            else:
                logger.warning(f"Server responded with status code {response.status_code}. Retrying...")
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}: Server not responding. Error: {e}. Retrying...")
        time.sleep(2)  # Wait before retrying

    logger.info("Server is not running. Starting the server...")
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
    subprocess.run(["make", "run-with-redis"], check=True, timeout=60, cwd=project_root)
    time.sleep(5)  # Wait for the server to start
    logger.info("Waiting a couple of seconds after starting the server...")
    time.sleep(2)  # Additional wait time
    response = requests.get("http://localhost:8000/api/ping", timeout=10)
    if response.status_code != 200:
        logger.error(f"Response status code: {response.status_code}")
        logger.error(f"Response content: {response.text}")
    assert response.status_code == 200, "Server failed to start"
    logger.info("Server started successfully.")

# Test getting subscriptions
@pytest.mark.parametrize("refresh_cache", [False, True])
def test_get_subscriptions(refresh_cache):
    logger.info(f"Starting test for getting subscriptions with refresh_cache={refresh_cache}...")
    ensure_redis_running()
    ensure_server_running()

    start_time = time.time()
    response = requests.get(
        "http://localhost:8000/api/subscriptions/", params={"refresh-cache": refresh_cache}, timeout=30
    )
    end_time = time.time()

    if response.status_code != 200:
        logger.error(f"Response status code: {response.status_code}")
        logger.error(f"Response content: {response.text}")
    assert response.status_code == 200, "Failed to fetch subscriptions"

    elapsed_time = end_time - start_time
    logger.info(f"Time taken with refresh_cache={refresh_cache}: {elapsed_time:.2f} seconds")

    # Calculate and log speedup if caching is enabled
    if refresh_cache:
        if not hasattr(test_get_subscriptions, "no_cache_time"):
            logger.error("No baseline time recorded for no-cache scenario. Cannot calculate speedup.")
        else:
            speedup = test_get_subscriptions.no_cache_time / elapsed_time if elapsed_time > 0 else float('inf')
            logger.info(f"Speedup with caching: {speedup:.2f}x")
    else:
        test_get_subscriptions.no_cache_time = elapsed_time

# Test getting resource groups
@pytest.mark.parametrize("refresh_cache", [False, True])
def test_get_resource_groups(refresh_cache):
    logger.info(f"Starting test for getting resource groups with refresh_cache={refresh_cache}...")
    ensure_redis_running()
    ensure_server_running()

    # Step 1: Get subscriptions
    logger.info("Fetching subscriptions...")
    subscriptions_response = requests.get(
        "http://localhost:8000/api/subscriptions/", params={"refresh-cache": refresh_cache}, timeout=30
    )
    if subscriptions_response.status_code != 200:
        logger.error(f"Response status code: {subscriptions_response.status_code}")
        logger.error(f"Response content: {subscriptions_response.text}")
    assert subscriptions_response.status_code == 200, "Failed to fetch subscriptions"
    subscriptions = subscriptions_response.json()

    # Step 2: Get resource groups for each subscription
    for subscription in subscriptions:
        subscription_id = subscription.get("id")
        logger.info(f"Fetching resource groups for subscription_id={subscription_id}...")

        start_time = time.time()
        resource_groups_response = requests.get(
            f"http://localhost:8000/api/subscriptions/{subscription_id}/resource-groups/",
            params={"refresh-cache": refresh_cache},
            timeout=30
        )
        end_time = time.time()

        if resource_groups_response.status_code != 200:
            logger.error(f"Response status code: {resource_groups_response.status_code}")
            logger.error(f"Response content: {resource_groups_response.text}")
        assert resource_groups_response.status_code == 200, f"Failed to fetch resource groups for subscription_id={subscription_id}"

        elapsed_time = end_time - start_time
        logger.info(f"Time taken for subscription_id={subscription_id} with refresh_cache={refresh_cache}: {elapsed_time:.2f} seconds")

# Test getting virtual machines
@pytest.mark.parametrize("refresh_cache", [False, True])
def test_get_virtual_machines(refresh_cache):
    logger.info(f"Starting test for getting virtual machines with refresh_cache={refresh_cache}...")
    ensure_redis_running()
    ensure_server_running()

    # Step 1: Get subscriptions
    logger.info("Fetching subscriptions...")
    subscriptions_response = requests.get(
        "http://localhost:8000/api/subscriptions/", params={"refresh-cache": refresh_cache}, timeout=30
    )
    if subscriptions_response.status_code != 200:
        logger.error(f"Response status code: {subscriptions_response.status_code}")
        logger.error(f"Response content: {subscriptions_response.text}")
    assert subscriptions_response.status_code == 200, "Failed to fetch subscriptions"
    subscriptions = subscriptions_response.json()

    # Step 2: Choose the first subscription
    if not subscriptions:
        pytest.fail("No subscriptions found")
    subscription_id = subscriptions[0].get("id")
    logger.info(f"Using subscription_id={subscription_id}")

    # Step 3: Get resource groups for the chosen subscription
    logger.info(f"Fetching resource groups for subscription_id={subscription_id}...")
    resource_groups_response = requests.get(
        f"http://localhost:8000/api/subscriptions/{subscription_id}/resource-groups/",
        params={"refresh-cache": refresh_cache},
        timeout=30
    )
    if resource_groups_response.status_code != 200:
        logger.error(f"Response status code: {resource_groups_response.status_code}")
        logger.error(f"Response content: {resource_groups_response.text}")
    assert resource_groups_response.status_code == 200, f"Failed to fetch resource groups for subscription_id={subscription_id}"
    resource_groups = resource_groups_response.json()

    # Step 4: Iterate through resource groups to find virtual machines
    for resource_group in resource_groups:
        resource_group_name = resource_group.get("name")
        logger.info(f"Fetching virtual machines for resource_group_name={resource_group_name}...")

        start_time = time.time()
        virtual_machines_response = requests.get(
            f"http://localhost:8000/api/subscriptions/{subscription_id}/resource-groups/{resource_group_name}/virtual-machines/",
            params={"refresh-cache": refresh_cache},
            timeout=30
        )
        end_time = time.time()

        if virtual_machines_response.status_code != 200:
            logger.error(f"Response status code: {virtual_machines_response.status_code}")
            logger.error(f"Response content: {virtual_machines_response.text}")
        assert virtual_machines_response.status_code == 200, f"Failed to fetch virtual machines for resource_group_name={resource_group_name}"

        virtual_machines = virtual_machines_response.json()
        elapsed_time = end_time - start_time
        logger.info(f"Time taken for resource_group_name={resource_group_name} with refresh_cache={refresh_cache}: {elapsed_time:.2f} seconds")

        if isinstance(virtual_machines, list) and len(virtual_machines) > 0:  # Stop if a non-empty list is found
            vm_names = [vm.get("name") for vm in virtual_machines]
            logger.info(f"Found virtual machines in resource_group_name={resource_group_name}: {vm_names}")
            break
        else:
            logger.info(f"No virtual machines found in resource_group_name={resource_group_name}. Continuing to the next resource group...")
    else:
        pytest.fail("No virtual machines found in any resource group")

# Test getting virtual machine details
@pytest.mark.parametrize("refresh_cache", [False, True])
def test_get_virtual_machine_details(refresh_cache):
    logger.info(f"Starting test for getting virtual machine details with refresh_cache={refresh_cache}...")
    ensure_redis_running()
    ensure_server_running()

    # Step 1: Get subscriptions
    logger.info("Fetching subscriptions...")
    subscriptions_response = requests.get(
        "http://localhost:8000/api/subscriptions/", params={"refresh-cache": refresh_cache}, timeout=30
    )
    if subscriptions_response.status_code != 200:
        logger.error(f"Response status code: {subscriptions_response.status_code}")
        logger.error(f"Response content: {subscriptions_response.text}")
    assert subscriptions_response.status_code == 200, "Failed to fetch subscriptions"
    subscriptions = subscriptions_response.json()

    # Step 2: Choose the first subscription
    if not subscriptions:
        pytest.fail("No subscriptions found")
    subscription_id = subscriptions[0].get("id")
    logger.info(f"Using subscription_id={subscription_id}")

    # Step 3: Get resource groups for the chosen subscription
    logger.info(f"Fetching resource groups for subscription_id={subscription_id}...")
    resource_groups_response = requests.get(
        f"http://localhost:8000/api/subscriptions/{subscription_id}/resource-groups/",
        params={"refresh-cache": refresh_cache},
        timeout=30
    )
    if resource_groups_response.status_code != 200:
        logger.error(f"Response status code: {resource_groups_response.status_code}")
        logger.error(f"Response content: {resource_groups_response.text}")
    assert resource_groups_response.status_code == 200, f"Failed to fetch resource groups for subscription_id={subscription_id}"
    resource_groups = resource_groups_response.json()

    # Step 4: Iterate through resource groups to find virtual machines
    for resource_group in resource_groups:
        resource_group_name = resource_group.get("name")
        logger.info(f"Fetching virtual machines for resource_group_name={resource_group_name}...")

        virtual_machines_response = requests.get(
            f"http://localhost:8000/api/subscriptions/{subscription_id}/resource-groups/{resource_group_name}/virtual-machines/",
            params={"refresh-cache": refresh_cache},
            timeout=30
        )
        if virtual_machines_response.status_code != 200:
            logger.error(f"Response status code: {virtual_machines_response.status_code}")
            logger.error(f"Response content: {virtual_machines_response.text}")
        assert virtual_machines_response.status_code == 200, f"Failed to fetch virtual machines for resource_group_name={resource_group_name}"

        virtual_machines = virtual_machines_response.json()
        if isinstance(virtual_machines, list) and len(virtual_machines) > 0:  # Stop if a non-empty list is found
            vm_names = [vm.get("name") for vm in virtual_machines]
            logger.info(f"Found virtual machines in resource_group_name={resource_group_name}: {vm_names}")

            # Step 5: Get details for the first virtual machine
            vm_name = vm_names[0]
            logger.info(f"Fetching details for virtual machine vm_name={vm_name}...")

            start_time = time.time()
            vm_details_response = requests.get(
                f"http://localhost:8000/api/subscriptions/{subscription_id}/resource-groups/{resource_group_name}/virtual-machines/{vm_name}",
                params={"refresh-cache": refresh_cache},
                timeout=30
            )
            end_time = time.time()

            if vm_details_response.status_code != 200:
                logger.error(f"Response status code: {vm_details_response.status_code}")
                logger.error(f"Response content: {vm_details_response.text}")
            assert vm_details_response.status_code == 200, f"Failed to fetch details for virtual machine vm_name={vm_name}"

            elapsed_time = end_time - start_time
            logger.info(f"Time taken for vm_name={vm_name} with refresh_cache={refresh_cache}: {elapsed_time:.2f} seconds")
            break
        else:
            logger.info(f"No virtual machines found in resource_group_name={resource_group_name}. Continuing to the next resource group...")
    else:
        pytest.fail("No virtual machines found in any resource group")

# Test listing all virtual machines
@pytest.mark.parametrize("refresh_cache", [False, True])
def test_list_all_virtual_machines(refresh_cache):
    logger.info(f"Starting test for listing all virtual machines with refresh_cache={refresh_cache}...")
    ensure_redis_running()
    ensure_server_running()

    # Fetch all virtual machines
    logger.info("Fetching all virtual machines...")
    start_time = time.time()
    response = requests.get("http://localhost:8000/api/subscriptions/virtual_machines/", timeout=30)
    end_time = time.time()

    if response.status_code != 200:
        logger.error(f"Response status code: {response.status_code}")
        logger.error(f"Response content: {response.text}")
    assert response.status_code == 200, "Failed to fetch all virtual machines"

    virtual_machines = response.json()
    assert isinstance(virtual_machines, list) and len(virtual_machines) > 0, "No virtual machines found"

    elapsed_time = end_time - start_time
    logger.info(f"Time taken to fetch all virtual machines: {elapsed_time:.2f} seconds")
    logger.info(f"Found virtual machines: {[vm.get('name') for vm in virtual_machines]} if names are available")

# Test getting virtual machine by name
@pytest.mark.parametrize("refresh_cache", [False, True])
def test_get_vm_by_name(refresh_cache):
    logger.info(f"Starting test for getting virtual machine by name with refresh_cache={refresh_cache}...")
    ensure_redis_running()
    ensure_server_running()

    # Step 1: Fetch all virtual machines
    logger.info("Fetching all virtual machines...")
    all_vms_response = requests.get("http://localhost:8000/api/subscriptions/virtual_machines/", timeout=30)
    if all_vms_response.status_code != 200:
        logger.error(f"Response status code: {all_vms_response.status_code}")
        logger.error(f"Response content: {all_vms_response.text}")
    assert all_vms_response.status_code == 200, "Failed to fetch all virtual machines"

    all_virtual_machines = all_vms_response.json()
    assert isinstance(all_virtual_machines, list) and len(all_virtual_machines) > 0, "No virtual machines found"

    # Step 2: Use the first virtual machine
    chosen_vm = all_virtual_machines[0]
    vm_name = chosen_vm.get("name")
    assert vm_name, "First virtual machine does not have a name"
    logger.info(f"Using first virtual machine name: {vm_name}")

    # Step 3: Fetch details for the chosen virtual machine by name
    logger.info(f"Fetching details for virtual machine vm_name={vm_name}...")
    start_time = time.time()
    vm_details_response = requests.get(
        f"http://localhost:8000/api/subscriptions/virtual_machines/{vm_name}",
        timeout=30
    )
    end_time = time.time()

    if vm_details_response.status_code != 200:
        logger.error(f"Response status code: {vm_details_response.status_code}")
        logger.error(f"Response content: {vm_details_response.text}")
    assert vm_details_response.status_code == 200, f"Failed to fetch details for virtual machine vm_name={vm_name}"

    elapsed_time = end_time - start_time
    logger.info(f"Time taken to fetch details for vm_name={vm_name}: {elapsed_time:.2f} seconds")
    logger.info(f"Details for vm_name={vm_name}: {vm_details_response.json()}")

# Test listing VM hostnames
@pytest.mark.parametrize("refresh_cache", [False, True])
def test_list_vm_hostnames(refresh_cache):
    logger.info(f"Starting test for listing VM hostnames with refresh_cache={refresh_cache}...")
    ensure_redis_running()
    ensure_server_running()

    # Fetch VM hostnames
    logger.info("Fetching VM hostnames...")
    start_time = time.time()
    response = requests.get("http://localhost:8000/api/subscriptions/hostnames/", params={"refresh-cache": refresh_cache}, timeout=180)
    end_time = time.time()

    if response.status_code != 200:
        logger.error(f"Response status code: {response.status_code}")
        logger.error(f"Response content: {response.text}")
    assert response.status_code == 200, "Failed to fetch VM hostnames"

    vm_hostnames = response.json()
    assert isinstance(vm_hostnames, list) and len(vm_hostnames) > 0, "No VM hostnames found"

    elapsed_time = end_time - start_time
    logger.info(f"Time taken to fetch VM hostnames: {elapsed_time:.2f} seconds")
    logger.info(f"Found VM hostnames: {vm_hostnames}")

# Test getting route tables
@pytest.mark.parametrize("refresh_cache", [False, True])
def test_get_route_tables(refresh_cache):
    logger.info(f"Starting test for getting route tables with refresh_cache={refresh_cache}...")
    ensure_redis_running()
    ensure_server_running()

    # Step 1: Get subscriptions
    logger.info("Fetching subscriptions...")
    subscriptions_response = requests.get(
        "http://localhost:8000/api/subscriptions/", params={"refresh-cache": refresh_cache}, timeout=30
    )
    if subscriptions_response.status_code != 200:
        logger.error(f"Response status code: {subscriptions_response.status_code}")
        logger.error(f"Response content: {subscriptions_response.text}")
    assert subscriptions_response.status_code == 200, "Failed to fetch subscriptions"
    subscriptions = subscriptions_response.json()

    # Step 2: Iterate through subscriptions to find route tables
    for subscription in subscriptions:
        subscription_id = subscription.get("id")
        logger.info(f"Fetching route tables for subscription_id={subscription_id}...")

        start_time = time.time()
        route_tables_response = requests.get(
            f"http://localhost:8000/api/subscriptions/{subscription_id}/routetables",
            params={"refresh-cache": refresh_cache},
            timeout=30
        )
        end_time = time.time()

        if route_tables_response.status_code != 200:
            logger.error(f"Response status code: {route_tables_response.status_code}")
            logger.error(f"Response content: {route_tables_response.text}")
        assert route_tables_response.status_code == 200, f"Failed to fetch route tables for subscription_id={subscription_id}"

        route_tables = route_tables_response.json()
        elapsed_time = end_time - start_time
        logger.info(f"Time taken for subscription_id={subscription_id} with refresh_cache={refresh_cache}: {elapsed_time:.2f} seconds")

        if isinstance(route_tables, list) and len(route_tables) > 0:  # Stop if a non-empty list is found
            logger.info(f"Found route tables for subscription_id={subscription_id}: {route_tables}")
            break
        else:
            logger.info(f"No route tables found for subscription_id={subscription_id}. Continuing to the next subscription...")
    else:
        pytest.fail("No route tables found in any subscription")