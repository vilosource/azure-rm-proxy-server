from mcp.server import Server
from azure_rm_mcp_server.subscriptions_tool import register_subscriptions_tool
import asyncio

async def create_server():
    """Create and configure the MCP server"""
    server = Server()
    
    # Register available tools
    register_subscriptions_tool(server)
    
    # Add health check endpoint
    @server.on_health_check
    async def health_check():
        return {"status": "healthy"}
    
    return server

async def main():
    """Main async entrypoint"""
    try:
        server = await create_server()
        print("Starting MCP server on localhost:8080")
        await server.run("localhost", 8080)
    except Exception as e:
        print(f"Server error: {e}")
        raise

if __name__ == "__main__":
    # Use asyncio.run() for cleaner event loop management
    asyncio.run(main())
