    def execute(self, output=None):
        """
        Execute the worker's task to fetch all resources.

        Args:
            output (str): Optional file path to save the results.
        """
        from azure_rm_client.workers.virtual_machines_worker import VirtualMachinesWorker
        import os
        import json

        subscription_worker = SubscriptionsWorker()
        subscriptions = subscription_worker.execute()

        if output:
            os.makedirs(output, exist_ok=True)

        resource_group_worker = ResourceGroupsWorker()
        virtual_machine_worker = VirtualMachinesWorker()

        for subscription in subscriptions:
            subscription_id = subscription.get("id")
            if not subscription_id:
                continue

            resource_groups = resource_group_worker.execute(subscription_id=subscription_id)
            subscription_dir = os.path.join(output, subscription_id) if output else None

            if subscription_dir:
                os.makedirs(subscription_dir, exist_ok=True)

            for resource_group in resource_groups:
                resource_group_name = resource_group.get("name")
                if not resource_group_name:
                    continue

                virtual_machines = virtual_machine_worker.list_virtual_machines(
                    subscription_id=subscription_id, resource_group_name=resource_group_name
                )

                resource_group_dir = os.path.join(subscription_dir, resource_group_name) if subscription_dir else None

                if resource_group_dir:
                    os.makedirs(resource_group_dir, exist_ok=True)

                for vm in virtual_machines:
                    vm_name = vm.get("name")
                    if not vm_name:
                        continue

                    vm_details = virtual_machine_worker.get_virtual_machine_details(
                        subscription_id=subscription_id,
                        resource_group_name=resource_group_name,
                        vm_name=vm_name
                    )

                    if resource_group_dir:
                        vm_file = os.path.join(resource_group_dir, f"{vm_name}.json")
                        with open(vm_file, "w") as file:
                            json.dump(vm_details, file, indent=2)