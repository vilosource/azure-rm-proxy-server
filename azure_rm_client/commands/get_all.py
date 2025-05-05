from azure_rm_client.commands.base_command import BaseCommand
from azure_rm_client.commands import CommandRegistry
from azure_rm_client.workers.azurerm_api_worker import AzureRMApiWorker
from azure_rm_client.workers.resource_groups_worker import ResourceGroupsWorker
from azure_rm_client.workers.route_tables_worker import RouteTablesWorker
from azure_rm_client.workers.subscriptions_worker import SubscriptionsWorker
from azure_rm_client.workers.virtual_machines_worker import VirtualMachinesWorker
from azure_rm_client.workers.vm_hostnames_worker import VMHostnamesWorker
from azure_rm_client.workers.vm_reports_worker import VMReportsWorker
from azure_rm_client.workers.vm_shortcuts_worker import VMShortcutsWorker

import logging
import os
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

"""

This module contains the GetAllCommand class, which is responsible for fetching all resources
from the Azure API. It uses various worker classes to interact with different Azure services.
The command can be executed with the specified output file name.
"""



@CommandRegistry.register
class GetAllCommand(BaseCommand):
    @property
    def name(self) -> str:
        return "get-all"

    @property
    def description(self) -> str:
        return "Fetch all resources."

    @classmethod
    def configure_parser(cls, subparser):
        subparser.add_argument(
            "--output",
            required=False,
            default="infra-data",
            help="Specify the output file to save the results (default: infra-data)."
        )

    def execute(self):
        """
        Use worker classes to fetch data from different Azure services.
        Save the results to the specified output directory, creating it if necessary.
        """
        logger.debug("Starting execution of GetAllCommand")
        output_dir = self.args['output']  # Access output from the args dictionary
        logger.debug(f"Output directory: {output_dir}")
        os.makedirs(output_dir, exist_ok=True)

        subscriptions = self._fetch_and_save_subscriptions(output_dir)
        self._process_subscriptions(subscriptions, output_dir)
        self._generate_and_save_vm_report(output_dir)
        self._process_route_tables(subscriptions, output_dir)

    def _fetch_and_save_subscriptions(self, output_dir):
        """
        Fetch subscriptions and save them to a file.

        Args:
            output_dir (str): The directory to save the subscriptions file.

        Returns:
            list: A list of subscriptions.
        """
        logger.debug("Fetching subscriptions")
        subscription_worker = SubscriptionsWorker()
        subscriptions = subscription_worker.execute()
        logger.debug(f"Fetched subscriptions: {subscriptions}")

        subscriptions_file = os.path.join(output_dir, "subscriptions.json")
        with open(subscriptions_file, "w") as file:
            json.dump(subscriptions, file, indent=2)
        logger.debug(f"Subscriptions saved to {subscriptions_file}")

        return subscriptions

    def _process_subscriptions(self, subscriptions, output_dir):
        """
        Process each subscription to fetch resource groups and virtual machines.

        Args:
            subscriptions (list): A list of subscriptions.
            output_dir (str): The directory to save the results.
        """
        resource_group_worker = ResourceGroupsWorker()
        virtual_machine_worker = VirtualMachinesWorker()

        for subscription in subscriptions:
            subscription_id = subscription.get("id")
            if not subscription_id:
                logger.debug("Skipping subscription with no ID")
                continue

            resource_groups = resource_group_worker.execute(subscription_id=subscription_id)
            subscription_dir = os.path.join(output_dir, subscription_id)
            os.makedirs(subscription_dir, exist_ok=True)

            self._process_resource_groups(resource_groups, subscription_id, subscription_dir, virtual_machine_worker)

    def _process_resource_groups(self, resource_groups, subscription_id, subscription_dir, virtual_machine_worker):
        """
        Process each resource group to fetch virtual machines and their details.

        Args:
            resource_groups (list): A list of resource groups.
            subscription_id (str): The subscription ID.
            subscription_dir (str): The directory to save the resource group results.
            virtual_machine_worker (VirtualMachinesWorker): The worker to fetch virtual machine data.
        """
        for resource_group in resource_groups:
            resource_group_name = resource_group.get("name")
            if not resource_group_name:
                logger.debug("Skipping resource group with no name")
                continue

            resource_group_dir = os.path.join(subscription_dir, resource_group_name)
            os.makedirs(resource_group_dir, exist_ok=True)

            virtual_machines = virtual_machine_worker.list_virtual_machines(
                subscription_id=subscription_id, resource_group_name=resource_group_name
            )
            logger.debug(f"Fetched virtual machines for resource group {resource_group_name}: {virtual_machines}")

            self._process_virtual_machines(virtual_machines, subscription_id, resource_group_name, resource_group_dir, virtual_machine_worker)

    def _process_virtual_machines(self, virtual_machines, subscription_id, resource_group_name, resource_group_dir, virtual_machine_worker):
        """
        Process each virtual machine to fetch its details and save them to a file.

        Args:
            virtual_machines (list): A list of virtual machines.
            subscription_id (str): The subscription ID.
            resource_group_name (str): The resource group name.
            resource_group_dir (str): The directory to save the virtual machine results.
            virtual_machine_worker (VirtualMachinesWorker): The worker to fetch virtual machine details.
        """
        for vm in virtual_machines:
            vm_name = vm.get("name")
            if not vm_name:
                logger.debug("Skipping virtual machine with no name")
                continue

            vm_details = virtual_machine_worker.get_virtual_machine_details(
                subscription_id=subscription_id,
                resource_group_name=resource_group_name,
                vm_name=vm_name
            )
            logger.debug(f"Fetched details for virtual machine {vm_name}")

            vm_file = os.path.join(resource_group_dir, f"{vm_name}.json")
            with open(vm_file, "w") as file:
                json.dump(vm_details, file, indent=2)
            logger.debug(f"Virtual machine details saved to {vm_file}")

    def _generate_and_save_vm_report(self, output_dir):
        """
        Generate a virtual machine report and save it to the output directory.

        Args:
            output_dir (str): The directory to save the report.
        """
        from azure_rm_client.workers.vm_reports_worker import VMReportsWorker
        import os
        import json

        logger.debug("Generating virtual machine report")
        report_worker = VMReportsWorker()
        vm_report = report_worker.execute(refresh_cache=False)

        reports_dir = os.path.join(output_dir, "reports")
        os.makedirs(reports_dir, exist_ok=True)

        report_file = os.path.join(reports_dir, "virtual-machine-report.json")
        with open(report_file, "w") as file:
            json.dump(vm_report, file, indent=2)

        logger.debug(f"Virtual machine report saved to {report_file}")

    def _process_route_tables(self, subscriptions, output_dir):
        """
        Process each subscription to fetch and save route tables.

        Args:
            subscriptions (list): A list of subscriptions.
            output_dir (str): The directory to save the results.
        """
        from azure_rm_client.workers.route_tables_worker import RouteTablesWorker
        route_tables_worker = RouteTablesWorker()

        for subscription in subscriptions:
            subscription_id = subscription.get("id")
            if not subscription_id:
                logger.debug("Skipping subscription with no ID")
                continue

            logger.debug(f"Processing route tables for subscription {subscription_id}")
            subscription_dir = os.path.join(output_dir, subscription_id)
            os.makedirs(subscription_dir, exist_ok=True)

            # Create a directory for route tables in this subscription
            route_tables_dir = os.path.join(subscription_dir, "route_tables")
            os.makedirs(route_tables_dir, exist_ok=True)

            try:
                # List all route tables in the subscription
                route_tables = route_tables_worker.list_route_tables(subscription_id=subscription_id)
                logger.debug(f"Found {len(route_tables)} route tables in subscription {subscription_id}")

                # Save the list of route tables
                route_tables_list_file = os.path.join(route_tables_dir, "route_tables.json")
                with open(route_tables_list_file, "w") as file:
                    json.dump(route_tables, file, indent=2)
                logger.debug(f"Route tables list saved to {route_tables_list_file}")

                # Process each route table to get details
                for route_table in route_tables:
                    route_table_name = route_table.get("name")
                    resource_group = route_table.get("resource_group")
                    
                    if not route_table_name or not resource_group:
                        logger.debug("Skipping route table with missing name or resource group")
                        continue

                    try:
                        # Get detailed information about the route table
                        route_table_details = route_tables_worker.get_route_table_details(
                            subscription_id=subscription_id,
                            resource_group_name=resource_group,
                            route_table_name=route_table_name
                        )
                        
                        # Save the route table details
                        route_table_file = os.path.join(route_tables_dir, f"{route_table_name}.json")
                        with open(route_table_file, "w") as file:
                            json.dump(route_table_details, file, indent=2)
                        logger.debug(f"Route table details saved to {route_table_file}")

                    except Exception as e:
                        logger.warning(f"Error processing route table {route_table_name}: {e}")
                        continue
            
            except Exception as e:
                logger.warning(f"Error fetching route tables for subscription {subscription_id}: {e}")
                continue

