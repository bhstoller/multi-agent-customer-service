import time

MCP_TOOLS = [
    {
        "name": "get_time",
        "description": "Return the current server time.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "greet_user",
        "description": "Return a greeting for the given user.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            },
            "required": ["name"]
        },
    },
]

# TOOL IMPLEMENTATIONS
def tool_get_time(_args: dict):
    """Returns current server time."""
    return {"time": time.ctime()}


def tool_greet_user(args: dict):
    """Returns greeting text."""
    name = args.get("name", "there")
    return {"message": f"Hello, {name}! Welcome to the MCP server."}

# TOOL DISPATCHER
def execute_tool(name: str, arguments: dict):
    """Dispatch tool calls based on name."""
    
    if name == "get_time":
        return tool_get_time(arguments)

    if name == "greet_user":
        return tool_greet_user(arguments)

    # If not found
    raise ValueError(f"Unknown tool: {name}")
