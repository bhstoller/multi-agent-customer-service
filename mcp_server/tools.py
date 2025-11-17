from typing import Dict, Any
from .db import (
    get_customer,
    list_customers,
    update_customer,
    create_ticket,
    get_customer_history,
)

# Define the MCP Tool Definitions

MCP_TOOLS = [
    {
        "name": "get_customer",
        "description": "Fetch customer information by customer_id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "integer"},
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "list_customers",
        "description": "List customers filtered by optional status, with limit.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "limit": {"type": "integer"},
            },
            "required": [],
        },
    },
    {
        "name": "update_customer",
        "description": "Update customer fields (name, email, phone, status).",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "integer"},
                "data": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"},
                        "phone": {"type": "string"},
                        "status": {"type": "string"},
                    },
                },
            },
            "required": ["customer_id", "data"],
        },
    },
    {
        "name": "create_ticket",
        "description": "Create a new support ticket for a customer.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "integer"},
                "issue": {"type": "string"},
                "priority": {"type": "string"},
            },
            "required": ["customer_id", "issue"],
        },
    },
    {
        "name": "get_customer_history",
        "description": "Retrieve all tickets for a customer.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "integer"},
            },
            "required": ["customer_id"],
        },
    },
]

# Define the Tool Routing Table

TOOLS_MAP = {
    "get_customer": lambda args: get_customer(args["customer_id"]),
    "list_customers": lambda args: list_customers(
        status=args.get("status"), limit=args.get("limit", 10)
    ),
    "update_customer": lambda args: update_customer(
        args["customer_id"], args["data"]
    ),
    "create_ticket": lambda args: create_ticket(
        args["customer_id"], args["issue"], args.get("priority", "medium")
    ),
    "get_customer_history": lambda args: get_customer_history(
        args["customer_id"]
    ),
}


# Define Tool Execution Helper Function
def execute_tool(tool_name: str, arguments: Dict[str, Any]):
    """Called by server.py when a tool is invoked."""
    if tool_name not in TOOLS_MAP:
        raise ValueError(f"Unknown MCP tool: {tool_name}")
    return TOOLS_MAP[tool_name](arguments)