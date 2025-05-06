from mcp.server.lowlevel import Server
from azure_rm_client.workers.subscriptions_worker import SubscriptionsWorker
import logging
import mcp.types as types

logger = logging.getLogger(__name__)

class SubscriptionsTool:
    """MCP tool for Azure subscription operations"""
    
    def __init__(self):
        self.worker = SubscriptionsWorker()
    
    async def list_subscriptions(self, arguments=None):
        """Handle list_subscriptions tool call"""
        try:
            logger.info("Processing list_subscriptions request")
            
            # Get subscriptions from the worker using the proxy server
            subscriptions = self.worker.list_subscriptions(refresh_cache=True)
            
            # Return data as text content
            result = {
                "status": "success",
                "subscriptions": subscriptions
            }
            
            return [types.TextContent(type="text", text=str(result))]
        except Exception as e:
            logger.error(f"Error in list_subscriptions: {str(e)}")
            error_result = {
                "status": "error",
                "message": str(e)
            }
            return [types.TextContent(type="text", text=str(error_result))]

def register_subscriptions_tool(server: Server):
    """Register subscriptions tool with MCP server"""
    tool = SubscriptionsTool()
    
    @server.call_tool()
    async def handle_tool_calls(name: str, arguments: dict):
        if name == "list_subscriptions":
            return await tool.list_subscriptions(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    @server.list_tools()
    async def list_tools():
        return [
            types.Tool(
                name="list_subscriptions",
                description="Get list of Azure subscriptions for the authenticated user",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            )
        ]
