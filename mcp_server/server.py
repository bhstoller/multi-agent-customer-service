from mcp.server.fastmcp import FastMCP
from .tools import MCP_TOOLS, execute_tool


# Initialize MCP server
mcp = FastMCP("customer-support-server")


# Register tool definitions
for tool in MCP_TOOLS:
    mcp.tool(
        name=tool["name"],
        description=tool["description"],
        input_schema=tool["input_schema"],
    )


# Handle tool calls
@mcp.call_tool()
def handle_tool_call(name: str, arguments: dict):
    return execute_tool(name, arguments)


# Run server
if __name__ == "__main__":
    mcp.run()