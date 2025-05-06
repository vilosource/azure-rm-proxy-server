 Enhancing MCP Client Context with Python SDK Tools
This guide outlines how to expose your Python SDK functions as tools within your MCP server and provide contextual guidance to the AI client for effective utilization.

1. Expose SDK Functions as MCP Tools
Use the @mcp.tool() decorator to register your SDK functions as tools within your MCP server. This makes them discoverable and callable by the client.

python
Copy
Edit
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Azure Resource Manager")

@mcp.tool()
def list_subscriptions() -> list[str]:
    """List all Azure subscriptions."""
    # Implementation here
    return ["subscription1", "subscription2"]

@mcp.tool()
def list_resource_groups(subscription_id: str) -> list[str]:
    """List resource groups within a subscription."""
    # Implementation here
    return ["resource_group1", "resource_group2"]

@mcp.tool()
def list_virtual_machines(subscription_id: str, resource_group: str) -> list[str]:
    """List virtual machines within a resource group."""
    # Implementation here
    return ["vm1", "vm2"]
2. Provide Descriptive Docstrings
Ensure each tool has a clear and concise docstring. These descriptions help the AI client understand the purpose and usage of each tool, facilitating better decision-making on when to invoke them.

3. Implement Resources for Contextual Data
Use the @mcp.resource() decorator to expose static or dynamic data that can provide context to the AI client. For example, you might expose a list of available subscriptions or resource groups:

python
Copy
Edit
@mcp.resource("subscriptions://list")
def get_subscriptions() -> list[str]:
    """Retrieve a list of available subscriptions."""
    # Implementation here
    return ["subscription1", "subscription2"]
Resources act as reference data that the AI client can use to make informed decisions.
Artificial Intelligence in Plain English
+2
GitHub
+2
lts-help.its.virginia.edu
+2

4. Utilize Prompts for Guided Interactions
Define prompts using the @mcp.prompt() decorator to guide the AI client's interactions. Prompts can provide templates or structured guidance on how to use the tools effectively.

python
Copy
Edit
@mcp.prompt()
def list_resources_prompt() -> str:
    return (
        "To list resources, first select a subscription using 'list_subscriptions', "
        "then choose a resource group with 'list_resource_groups', "
        "and finally list virtual machines using 'list_virtual_machines'."
    )
Prompts help the AI client understand the sequence and context in which tools should be used.

5. Leverage the Context Object for Enhanced Interactions
The Context object in MCP provides capabilities such as logging, progress reporting, and resource reading. By incorporating the Context object into your tools, you can offer real-time feedback and richer interactions.

python
Copy
Edit
from mcp.server.fastmcp import Context

@mcp.tool()
async def list_virtual_machines(subscription_id: str, resource_group: str, ctx: Context) -> list[str]:
    """List virtual machines within a resource group."""
    ctx.info(f"Fetching VMs for subscription: {subscription_id}, resource group: {resource_group}")
    # Implementation here
    return ["vm1", "vm2"]
Using ctx.info() allows you to send informational messages back to the client, enhancing transparency and user experience.

6. Test and Iterate
After setting up your tools, resources, and prompts, test the interactions to ensure the AI client behaves as expected. Iteratively refine the docstrings, prompts, and resource data to improve clarity and usability.

By systematically exposing your Python SDK functions as MCP tools, providing descriptive metadata, and leveraging resources and prompts, you equip your MCP client with the necessary context to utilize these tools effectively. This structured approach enhances the AI client's ability to make informed decisions and perform tasks efficiently.


