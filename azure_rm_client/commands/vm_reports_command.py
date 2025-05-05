from azure_rm_client.commands.base_command import BaseCommand
from azure_rm_client.commands import CommandRegistry
from azure_rm_client.workers.vm_reports_worker import VMReportsWorker
import logging
import json

logger = logging.getLogger(__name__)

@CommandRegistry.register
class VMReportsCommand(BaseCommand):
    @property
    def name(self) -> str:
        return "vm-reports"

    @property
    def description(self) -> str:
        return "Generate and manage VM reports."

    @classmethod
    def configure_parser(cls, subparser):
        # Configure command options
        subparser.add_argument("--refresh-cache", action="store_true", help="Refresh the cache")
        subparser.add_argument("--output", help="Output file to save the report (optional)")

    def execute(self):
        """Generate a virtual machine report."""
        refresh_cache = self.args.get('refresh_cache', False)
        output_file = self.args.get('output')

        logger.debug("Generating VM report")
        
        try:
            # Initialize the worker
            report_worker = VMReportsWorker()
            
            # Generate the report
            vm_report = report_worker.execute(refresh_cache=refresh_cache)
            
            # Output the report
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(vm_report, f, indent=2)
                print(f"VM report saved to {output_file}")
            else:
                print(json.dumps(vm_report, indent=2))
                
            logger.debug(f"Generated VM report with {len(vm_report)} entries")
            
        except Exception as e:
            logger.error(f"Error generating VM report: {e}")
            print(f"Error: {e}")