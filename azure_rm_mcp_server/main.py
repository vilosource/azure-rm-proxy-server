#!/usr/bin/env python
"""
Azure Resource Manager MCP Server
Exposes Azure RM functionality via the Model Context Protocol
"""
import asyncio
import logging
from mcp.server.lowlevel import Server
from azure_rm_mcp_server.tools import register_all_tools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("logs/mcp_server.log")],
)
logger = logging.getLogger(__name__)


async def create_server():
    """Create and configure the MCP server"""
    server = Server("azure-rm-mcp")

    # Register all available tools (including subscriptions tool)
    register_all_tools(server)
    logger.info("Registered all Azure RM tools")

    return server


async def main():
    """Main async entrypoint"""
    try:
        logger.info("Starting Azure RM MCP Server")
        server = await create_server()

        # The Server.run method expects input/output streams and initialization options
        # For VSCode integration, we'll use stdio (standard input/output)
        from mcp.server.stdio import stdio_server

        async with stdio_server() as streams:
            logger.info("MCP server started with stdio transport")
            await server.run(streams[0], streams[1], server.create_initialization_options())
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


def start():
    """Start the MCP server (entry point for script)"""
    asyncio.run(main())


if __name__ == "__main__":
    start()
