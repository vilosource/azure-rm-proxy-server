"""
MCP tools implementations for Azure RM Proxy Server
This module provides Model Context Protocol tools for all available workers
"""

from mcp.server.lowlevel import Server
import logging
import mcp.types as types
import requests

from azure_rm_client.workers import (
    AzureRMApiWorker,
    ResourceGroupsWorker,
    RouteTablesWorker,
    SubscriptionsWorker,
    VirtualMachinesWorker,
    VMHostnamesWorker,
    VMReportsWorker,
    VMShortcutsWorker,
)
from azure_rm_client.client import RestClient, RequestsHttpClient, JsonResponseHandler

logger = logging.getLogger(__name__)

# Create RestClient for AzureRMApiWorker
API_BASE_URL = "http://localhost:8000/api"
http_client = RequestsHttpClient()
response_handler = JsonResponseHandler()
rest_client = RestClient(API_BASE_URL, http_client, response_handler)


class SubscriptionsTool:
    """MCP tool for Azure subscription operations"""

    def __init__(self):
        self.worker = SubscriptionsWorker()

    async def list_subscriptions(self, arguments=None):
        """Handle list_subscriptions tool call"""
        try:
            logger.info("Processing list_subscriptions request")
            refresh_cache = arguments.get("refresh_cache", False) if arguments else False

            # Get subscriptions from the worker using the proxy server
            subscriptions = self.worker.list_subscriptions(refresh_cache=refresh_cache)

            # Return data as text content
            result = {"status": "success", "subscriptions": subscriptions}

            return [types.TextContent(type="text", text=str(result))]
        except Exception as e:
            logger.error(f"Error in list_subscriptions: {str(e)}")
            error_result = {"status": "error", "message": str(e)}
            return [types.TextContent(type="text", text=str(error_result))]


class ResourceGroupsTool:
    """MCP tool for Azure resource groups operations"""

    def __init__(self):
        self.worker = ResourceGroupsWorker()

    async def list_resource_groups(self, arguments):
        """Handle list_resource_groups tool call"""
        try:
            logger.info("Processing list_resource_groups request")
            subscription_id = arguments.get("subscription_id")
            refresh_cache = arguments.get("refresh_cache", False)

            if not subscription_id:
                error_msg = "subscription_id is required"
                logger.error(error_msg)
                return [
                    types.TextContent(
                        type="text", text=str({"status": "error", "message": error_msg})
                    )
                ]

            resource_groups = self.worker.execute(
                subscription_id=subscription_id, refresh_cache=refresh_cache
            )

            result = {"status": "success", "resource_groups": resource_groups}

            return [types.TextContent(type="text", text=str(result))]
        except Exception as e:
            logger.error(f"Error in list_resource_groups: {str(e)}")
            error_result = {"status": "error", "message": str(e)}
            return [types.TextContent(type="text", text=str(error_result))]


class VirtualMachinesTool:
    """MCP tool for Azure virtual machines operations"""

    def __init__(self):
        self.worker = VirtualMachinesWorker()

    async def list_virtual_machines(self, arguments):
        """Handle list_virtual_machines tool call"""
        try:
            logger.info("Processing list_virtual_machines request")
            subscription_id = arguments.get("subscription_id")
            resource_group = arguments.get("resource_group")
            refresh_cache = arguments.get("refresh_cache", False)

            if not subscription_id:
                error_msg = "subscription_id is required"
                logger.error(error_msg)
                return [
                    types.TextContent(
                        type="text", text=str({"status": "error", "message": error_msg})
                    )
                ]

            if not resource_group:
                error_msg = "resource_group is required"
                logger.error(error_msg)
                return [
                    types.TextContent(
                        type="text", text=str({"status": "error", "message": error_msg})
                    )
                ]

            virtual_machines = self.worker.list_virtual_machines(
                subscription_id=subscription_id,
                resource_group_name=resource_group,  # Fixed: Changed parameter name to match worker method
                refresh_cache=refresh_cache,
            )

            result = {"status": "success", "virtual_machines": virtual_machines}

            return [types.TextContent(type="text", text=str(result))]
        except Exception as e:
            logger.error(f"Error in list_virtual_machines: {str(e)}")
            error_result = {"status": "error", "message": str(e)}
            return [types.TextContent(type="text", text=str(error_result))]

    async def get_virtual_machine(self, arguments):
        """Handle get_virtual_machine tool call"""
        try:
            logger.info("Processing get_virtual_machine request")
            subscription_id = arguments.get("subscription_id")
            resource_group = arguments.get("resource_group")
            vm_name = arguments.get("vm_name")
            refresh_cache = arguments.get("refresh_cache", False)

            if not subscription_id or not resource_group or not vm_name:
                error_msg = "subscription_id, resource_group, and vm_name are required"
                logger.error(error_msg)
                return [
                    types.TextContent(
                        type="text", text=str({"status": "error", "message": error_msg})
                    )
                ]

            vm_details = self.worker.get_virtual_machine_details(  # Fixed: Changed method name to match worker method
                subscription_id=subscription_id,
                resource_group_name=resource_group,  # Fixed: Changed parameter name to match worker method
                vm_name=vm_name,
                refresh_cache=refresh_cache,
            )

            result = {"status": "success", "virtual_machine": vm_details}

            return [types.TextContent(type="text", text=str(result))]
        except Exception as e:
            logger.error(f"Error in get_virtual_machine: {str(e)}")
            error_result = {"status": "error", "message": str(e)}
            return [types.TextContent(type="text", text=str(error_result))]


class RouteTablesTool:
    """MCP tool for Azure route tables operations"""

    def __init__(self):
        self.worker = RouteTablesWorker()

    async def list_route_tables(self, arguments):
        """Handle list_route_tables tool call"""
        try:
            logger.info("Processing list_route_tables request")
            subscription_id = arguments.get("subscription_id")
            resource_group = arguments.get("resource_group")
            refresh_cache = arguments.get("refresh_cache", False)

            if not subscription_id:
                error_msg = "subscription_id is required"
                logger.error(error_msg)
                return [
                    types.TextContent(
                        type="text", text=str({"status": "error", "message": error_msg})
                    )
                ]

            # Use the worker's execute method which can handle the resource_group parameter
            # through its operation parameter handling
            route_tables = self.worker.execute(
                operation="list_route_tables",
                subscription_id=subscription_id,
                refresh_cache=refresh_cache,
            )

            result = {"status": "success", "route_tables": route_tables}

            return [types.TextContent(type="text", text=str(result))]
        except Exception as e:
            logger.error(f"Error in list_route_tables: {str(e)}")
            error_result = {"status": "error", "message": str(e)}
            return [types.TextContent(type="text", text=str(error_result))]


class VMHostnamesTool:
    """MCP tool for Azure VM hostnames operations"""

    def __init__(self):
        self.worker = VMHostnamesWorker()

    async def get_vm_hostnames(self, arguments):
        """Handle get_vm_hostnames tool call"""
        try:
            logger.info("Processing get_vm_hostnames request")
            subscription_id = arguments.get("subscription_id")
            resource_group = arguments.get("resource_group")
            refresh_cache = arguments.get("refresh_cache", False)

            if not subscription_id:
                error_msg = "subscription_id is required"
                logger.error(error_msg)
                return [
                    types.TextContent(
                        type="text", text=str({"status": "error", "message": error_msg})
                    )
                ]

            vm_hostnames = self.worker.list_vm_hostnames(
                subscription_id=subscription_id, refresh_cache=refresh_cache
            )

            result = {"status": "success", "vm_hostnames": vm_hostnames}

            return [types.TextContent(type="text", text=str(result))]
        except Exception as e:
            logger.error(f"Error in get_vm_hostnames: {str(e)}")
            error_result = {"status": "error", "message": str(e)}
            return [types.TextContent(type="text", text=str(error_result))]


class VMReportsTool:
    """MCP tool for Azure VM reports operations"""

    def __init__(self):
        self.worker = VMReportsWorker()

    async def generate_vm_report(self, arguments):
        """Handle generate_vm_report tool call"""
        try:
            logger.info("Processing generate_vm_report request")
            subscription_id = arguments.get("subscription_id")
            resource_group = arguments.get("resource_group")
            refresh_cache = arguments.get("refresh_cache", False)

            if not subscription_id:
                error_msg = "subscription_id is required"
                logger.error(error_msg)
                return [
                    types.TextContent(
                        type="text", text=str({"status": "error", "message": error_msg})
                    )
                ]

            vm_report = self.worker.generate_vm_report(refresh_cache=refresh_cache)

            result = {"status": "success", "vm_report": vm_report}

            return [types.TextContent(type="text", text=str(result))]
        except Exception as e:
            logger.error(f"Error in generate_vm_report: {str(e)}")
            error_result = {"status": "error", "message": str(e)}
            return [types.TextContent(type="text", text=str(error_result))]


class VMShortcutsTool:
    """MCP tool for Azure VM shortcuts operations"""

    def __init__(self):
        self.worker = VMShortcutsWorker()

    async def get_vm_shortcuts(self, arguments):
        """Handle get_vm_shortcuts tool call"""
        try:
            logger.info("Processing get_vm_shortcuts request")
            subscription_id = arguments.get("subscription_id")
            resource_group = arguments.get("resource_group")
            refresh_cache = arguments.get("refresh_cache", False)

            if not subscription_id:
                error_msg = "subscription_id is required"
                logger.error(error_msg)
                return [
                    types.TextContent(
                        type="text", text=str({"status": "error", "message": error_msg})
                    )
                ]

            # Use the list_all_virtual_machines method instead of the non-existent get_shortcuts
            vm_shortcuts = self.worker.list_all_virtual_machines(refresh_cache=refresh_cache)

            result = {"status": "success", "vm_shortcuts": vm_shortcuts}

            return [types.TextContent(type="text", text=str(result))]
        except Exception as e:
            logger.error(f"Error in get_vm_shortcuts: {str(e)}")
            error_result = {"status": "error", "message": str(e)}
            return [types.TextContent(type="text", text=str(error_result))]


class AzureRMApiTool:
    """MCP tool for general Azure RM API operations"""

    def __init__(self):
        # Initialize with the RestClient
        self.worker = AzureRMApiWorker(rest_client)

    async def fetch_azure_rm_api(self, arguments):
        """Handle fetch_azure_rm_api tool call"""
        try:
            logger.info("Processing fetch_azure_rm_api request")
            endpoint = arguments.get("endpoint")

            if not endpoint:
                error_msg = "endpoint is required"
                logger.error(error_msg)
                return [
                    types.TextContent(
                        type="text", text=str({"status": "error", "message": error_msg})
                    )
                ]

            api_result = self.worker.execute(endpoint=endpoint)

            result = {"status": "success", "api_result": api_result}

            return [types.TextContent(type="text", text=str(result))]
        except Exception as e:
            logger.error(f"Error in fetch_azure_rm_api: {str(e)}")
            error_result = {"status": "error", "message": str(e)}
            return [types.TextContent(type="text", text=str(error_result))]


def register_all_tools(server: Server):
    """Register all Azure RM tools with the MCP server"""
    # Initialize all tool instances
    subscriptions_tool = SubscriptionsTool()
    resource_groups_tool = ResourceGroupsTool()
    virtual_machines_tool = VirtualMachinesTool()
    route_tables_tool = RouteTablesTool()
    vm_hostnames_tool = VMHostnamesTool()
    vm_reports_tool = VMReportsTool()
    vm_shortcuts_tool = VMShortcutsTool()
    azurerm_api_tool = AzureRMApiTool()

    @server.call_tool()
    async def handle_tool_calls(name: str, arguments: dict):
        """Handle all MCP tool calls"""
        # Subscriptions
        if name == "list_subscriptions":
            return await subscriptions_tool.list_subscriptions(arguments)

        # Resource Groups
        if name == "list_resource_groups":
            return await resource_groups_tool.list_resource_groups(arguments)

        # Virtual Machines
        elif name == "list_virtual_machines":
            return await virtual_machines_tool.list_virtual_machines(arguments)
        elif name == "get_virtual_machine":
            return await virtual_machines_tool.get_virtual_machine(arguments)

        # Route Tables
        elif name == "list_route_tables":
            return await route_tables_tool.list_route_tables(arguments)

        # VM Hostnames
        elif name == "get_vm_hostnames":
            return await vm_hostnames_tool.get_vm_hostnames(arguments)

        # VM Reports
        elif name == "generate_vm_report":
            return await vm_reports_tool.generate_vm_report(arguments)

        # VM Shortcuts
        elif name == "get_vm_shortcuts":
            return await vm_shortcuts_tool.get_vm_shortcuts(arguments)

        # Azure RM API
        elif name == "fetch_azure_rm_api":
            return await azurerm_api_tool.fetch_azure_rm_api(arguments)

        else:
            raise ValueError(f"Unknown tool: {name}")

    @server.list_tools()
    async def list_tools():
        """List all available MCP tools"""
        return [
            # Subscriptions
            types.Tool(
                name="list_subscriptions",
                description="Get list of Azure subscriptions for the authenticated user",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "refresh_cache": {
                            "type": "boolean",
                            "description": "Whether to bypass cache and fetch fresh data",
                        }
                    },
                },
            ),
            # Resource Groups
            types.Tool(
                name="list_resource_groups",
                description="List resource groups in an Azure subscription",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "subscription_id": {
                            "type": "string",
                            "description": "The Azure subscription ID",
                        },
                        "refresh_cache": {
                            "type": "boolean",
                            "description": "Whether to bypass cache and fetch fresh data",
                        },
                    },
                    "required": ["subscription_id"],
                },
            ),
            # Virtual Machines
            types.Tool(
                name="list_virtual_machines",
                description="List virtual machines in an Azure subscription or resource group",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "subscription_id": {
                            "type": "string",
                            "description": "The Azure subscription ID",
                        },
                        "resource_group": {
                            "type": "string",
                            "description": "The resource group name (optional)",
                        },
                        "refresh_cache": {
                            "type": "boolean",
                            "description": "Whether to bypass cache and fetch fresh data",
                        },
                    },
                    "required": ["subscription_id"],
                },
            ),
            types.Tool(
                name="get_virtual_machine",
                description="Get details of a specific virtual machine",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "subscription_id": {
                            "type": "string",
                            "description": "The Azure subscription ID",
                        },
                        "resource_group": {
                            "type": "string",
                            "description": "The resource group name",
                        },
                        "vm_name": {"type": "string", "description": "The virtual machine name"},
                        "refresh_cache": {
                            "type": "boolean",
                            "description": "Whether to bypass cache and fetch fresh data",
                        },
                    },
                    "required": ["subscription_id", "resource_group", "vm_name"],
                },
            ),
            # Route Tables
            types.Tool(
                name="list_route_tables",
                description="List route tables in an Azure resource group",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "subscription_id": {
                            "type": "string",
                            "description": "The Azure subscription ID",
                        },
                        "resource_group": {
                            "type": "string",
                            "description": "The resource group name",
                        },
                        "refresh_cache": {
                            "type": "boolean",
                            "description": "Whether to bypass cache and fetch fresh data",
                        },
                    },
                    "required": ["subscription_id", "resource_group"],
                },
            ),
            # VM Hostnames
            types.Tool(
                name="get_vm_hostnames",
                description="Get hostnames for virtual machines in an Azure subscription or resource group",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "subscription_id": {
                            "type": "string",
                            "description": "The Azure subscription ID",
                        },
                        "resource_group": {
                            "type": "string",
                            "description": "The resource group name (optional)",
                        },
                        "refresh_cache": {
                            "type": "boolean",
                            "description": "Whether to bypass cache and fetch fresh data",
                        },
                    },
                    "required": ["subscription_id"],
                },
            ),
            # VM Reports
            types.Tool(
                name="generate_vm_report",
                description="Generate a report of virtual machines in an Azure subscription or resource group",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "subscription_id": {
                            "type": "string",
                            "description": "The Azure subscription ID",
                        },
                        "resource_group": {
                            "type": "string",
                            "description": "The resource group name (optional)",
                        },
                        "refresh_cache": {
                            "type": "boolean",
                            "description": "Whether to bypass cache and fetch fresh data",
                        },
                    },
                    "required": ["subscription_id"],
                },
            ),
            # VM Shortcuts
            types.Tool(
                name="get_vm_shortcuts",
                description="Get shortcuts for virtual machines in an Azure subscription or resource group",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "subscription_id": {
                            "type": "string",
                            "description": "The Azure subscription ID",
                        },
                        "resource_group": {
                            "type": "string",
                            "description": "The resource group name (optional)",
                        },
                        "refresh_cache": {
                            "type": "boolean",
                            "description": "Whether to bypass cache and fetch fresh data",
                        },
                    },
                    "required": ["subscription_id"],
                },
            ),
            # Azure RM API
            types.Tool(
                name="fetch_azure_rm_api",
                description="Make a direct call to the Azure RM API",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "endpoint": {"type": "string", "description": "The API endpoint path"},
                        "params": {
                            "type": "object",
                            "description": "Query parameters to include in the request",
                        },
                        "refresh_cache": {
                            "type": "boolean",
                            "description": "Whether to bypass cache and fetch fresh data",
                        },
                    },
                    "required": ["endpoint"],
                },
            ),
        ]
