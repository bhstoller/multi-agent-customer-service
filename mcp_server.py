"""
MCP Server for Customer Management System.

This module provides a Flask-based MCP (Model Context Protocol) server that exposes
customer management operations through standardized tools:
- get_customer: Retrieve customer by ID
- list_customers: List customers with optional status filter
- update_customer: Update customer information
- create_ticket: Create a support ticket
- get_customer_history: Get ticket history for a customer

The server implements the MCP protocol for JSON-RPC communication.
Optionally exposes the server via ngrok for public access.
"""

import sqlite3
import json
import logging
from typing import Optional, Dict, List, Any, Callable
from flask import Flask, request, Response, jsonify
from flask_cors import CORS
from config import DB_PATH, NGROK_AUTHTOKEN, USE_NGROK

# Import ngrok if configured
if USE_NGROK:
    try:
        from pyngrok import ngrok
    except ImportError:
        raise ImportError(
            "pyngrok is required when NGROK_AUTHTOKEN is set. "
            "Install it with: pip install pyngrok"
        )

# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress verbose logging from dependencies
logging.getLogger('flask').setLevel(logging.WARNING)
logging.getLogger('werkzeug').setLevel(logging.WARNING)
logging.getLogger('pyngrok').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

# ============================================================================
# DATABASE HELPER FUNCTIONS
# ============================================================================


def get_db_connection():
    """
    Create a database connection with row factory for dict-like access.
    
    Returns:
        sqlite3.Connection: A database connection with Row factory enabled.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """
    Convert a SQLite row to a dictionary.
    
    Args:
        row: A sqlite3.Row object from query results.
        
    Returns:
        Dict[str, Any]: Dictionary representation of the row.
    """
    return {key: row[key] for key in row.keys()}


# ============================================================================
# READ OPERATIONS
# ============================================================================


def get_customer(customer_id: int) -> Dict[str, Any]:
    """
    Retrieve a specific customer by ID.

    Args:
        customer_id: The unique ID of the customer

    Returns:
        Dict containing customer data or error message
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'success': True,
                'customer': row_to_dict(row)
            }
        else:
            return {
                'success': False,
                'error': f'Customer with ID {customer_id} not found'
            }
    except Exception as e:
        return {
            'success': False,
            'error': f'Database error: {str(e)}'
        }


def list_customers(status: Optional[str] = None) -> Dict[str, Any]:
    """
    List all customers, optionally filtered by status.

    Args:
        status: Optional filter - 'active', 'disabled', or None for all

    Returns:
        Dict containing list of customers or error message
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if status:
            if status not in ['active', 'disabled']:
                return {
                    'success': False,
                    'error': 'Status must be "active" or "disabled"'
                }
            cursor.execute('SELECT * FROM customers WHERE status = ? ORDER BY name', (status,))
        else:
            cursor.execute('SELECT * FROM customers ORDER BY name')

        rows = cursor.fetchall()
        conn.close()

        customers = [row_to_dict(row) for row in rows]

        return {
            'success': True,
            'count': len(customers),
            'customers': customers
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Database error: {str(e)}'
        }


def get_customer_history(customer_id: int) -> Dict[str, Any]:
    """
    Retrieve complete ticket history for a customer.

    Args:
        customer_id: The unique ID of the customer whose history is requested

    Returns:
        Dict containing the list of tickets or error message
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT * FROM tickets
            WHERE customer_id = ?
            ORDER BY created_at DESC
        """, (customer_id,))

        rows = cur.fetchall()
        conn.close()

        tickets = [row_to_dict(r) for r in rows]

        return {
            "success": True,
            "count": len(tickets),
            "history": tickets
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# UPDATE OPERATIONS
# ============================================================================


def update_customer(customer_id: int, name: Optional[str] = None,
                   email: Optional[str] = None, phone: Optional[str] = None) -> Dict[str, Any]:
    """
    Update customer information.

    Args:
        customer_id: The unique ID of the customer to update
        name: New name (optional)
        email: New email (optional)
        phone: New phone (optional)

    Returns:
        Dict containing updated customer data or error message
    """
    try:
        # Check if customer exists
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        if not cursor.fetchone():
            conn.close()
            return {
                'success': False,
                'error': f'Customer with ID {customer_id} not found'
            }

        # Build update query dynamically based on provided fields
        updates = []
        params = []

        if name is not None:
            updates.append('name = ?')
            params.append(name.strip())
        if email is not None:
            updates.append('email = ?')
            params.append(email)
        if phone is not None:
            updates.append('phone = ?')
            params.append(phone)

        if not updates:
            conn.close()
            return {
                'success': False,
                'error': 'No fields to update'
            }

        # Always update the updated_at timestamp
        updates.append('updated_at = CURRENT_TIMESTAMP')
        params.append(customer_id)

        update_clause = ', '.join(updates)
        query = f'UPDATE customers SET {update_clause} WHERE id = ?'
        cursor.execute(query, params)
        conn.commit()

        # Fetch updated customer
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        row = cursor.fetchone()
        conn.close()

        return {
            'success': True,
            'message': f'Customer {customer_id} updated successfully',
            'customer': row_to_dict(row)
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Database error: {str(e)}'
        }


# ============================================================================
# CREATE OPERATIONS
# ============================================================================


def create_ticket(customer_id: int,
                  issue: str,
                  priority: str) -> Dict[str, Any]:
    """
    Create a new support ticket for a customer.

    Args:
        customer_id: The ID of the customer creating the ticket
        issue: Description of the issue
        priority: Priority level ('low', 'medium', 'high')

    Returns:
        Dict containing created ticket data or error message
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Validate customer exists
        cur.execute("SELECT id FROM customers WHERE id = ?", (customer_id,))
        if not cur.fetchone():
            conn.close()
            return {"success": False, "error": f"Customer {customer_id} not found"}

        cur.execute("""
            INSERT INTO tickets (customer_id, issue, status, priority, created_at)
            VALUES (?, ?, 'open', ?, CURRENT_TIMESTAMP)
        """, (customer_id, issue, priority))

        ticket_id = cur.lastrowid
        conn.commit()

        cur.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        row = cur.fetchone()
        conn.close()

        return {
            "success": True,
            "ticket": row_to_dict(row)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# MCP TOOL DEFINITIONS
# ============================================================================

MCP_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "get_customer",
        "description": "Retrieve a customer record by its ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "integer",
                    "description": "The ID of the customer to retrieve."
                }
            },
            "required": ["customer_id"]
        }
    },
    {
        "name": "list_customers",
        "description": "List all customers, optionally filtered by status.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["active", "disabled"],
                    "description": "Filter by customer status (active or disabled). If omitted, returns all customers."
                }
            },
            "required": []
        }
    },
    {
        "name": "update_customer",
        "description": "Update customer information (name, email, phone).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "integer",
                    "description": "The ID of the customer to update."
                },
                "name": {
                    "type": "string",
                    "description": "New customer name (optional)."
                },
                "email": {
                    "type": "string",
                    "description": "New customer email (optional)."
                },
                "phone": {
                    "type": "string",
                    "description": "New customer phone number (optional)."
                }
            },
            "required": ["customer_id"]
        }
    },
    {
        "name": "create_ticket",
        "description": "Create a new support ticket for a customer.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "integer",
                    "description": "The ID of the customer creating the ticket."
                },
                "issue": {
                    "type": "string",
                    "description": "Description of the support issue."
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Priority level of the ticket."
                }
            },
            "required": ["customer_id", "issue", "priority"]
        }
    },
    {
        "name": "get_customer_history",
        "description": "Return all tickets associated with a customer.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "integer",
                    "description": "The customer whose ticket history will be retrieved."
                }
            },
            "required": ["customer_id"]
        }
    }
]


# ============================================================================
# MCP MESSAGE HANDLERS
# ============================================================================


def create_sse_message(data: Dict[str, Any]) -> str:
    """
    Format a message for Server-Sent Events (SSE).

    Args:
        data: A dictionary containing the MCP response payload.

    Returns:
        A formatted SSE string containing the JSON-encoded payload.
    """
    return f"data: {json.dumps(data)}\n\n"


def handle_initialize(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle an MCP initialize request.

    Args:
        message: The incoming MCP initialize request.

    Returns:
        A dictionary representing the MCP initialize response.
    """
    return {
        "jsonrpc": "2.0",
        "id": message.get("id"),
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {
                "name": "customer-management-server",
                "version": "1.0.0"
            }
        }
    }


def handle_tools_list(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return the list of available MCP tools.

    Args:
        message: The incoming MCP request.

    Returns:
        A dictionary containing the list of MCP tools.
    """
    return {
        "jsonrpc": "2.0",
        "id": message.get("id"),
        "result": {"tools": MCP_TOOLS}
    }


def handle_tools_call(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a requested MCP tool.

    Args:
        message: The incoming MCP tools/call request.

    Returns:
        A dictionary containing the tool execution result.
    """
    params = message.get("params", {})
    tool_name: str = params.get("name")
    arguments: Dict[str, Any] = params.get("arguments", {})

    tool_functions: Dict[str, Callable[..., Dict[str, Any]]] = {
        "get_customer": get_customer,
        "list_customers": list_customers,
        "update_customer": update_customer,
        "create_ticket": create_ticket,
        "get_customer_history": get_customer_history,
    }

    if tool_name not in tool_functions:
        return {
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "error": {
                "code": -32601,
                "message": f"Tool not found: {tool_name}"
            }
        }

    try:
        result = tool_functions[tool_name](**arguments)

        return {
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "result": {
                "content": [
                    {"type": "text", "text": json.dumps(result, indent=2)}
                ]
            }
        }

    except Exception as e:
        logger.error(f"Tool execution error for {tool_name}: {str(e)}")
        return {
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "error": {
                "code": -32603,
                "message": f"Tool execution error: {str(e)}"
            }
        }


def process_mcp_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Route an MCP request to the appropriate handler.

    Args:
        message: The incoming MCP request.

    Returns:
        A dictionary containing the MCP response.
    """
    method: str = message.get("method")

    if method == "initialize":
        return handle_initialize(message)
    if method == "tools/list":
        return handle_tools_list(message)
    if method == "tools/call":
        return handle_tools_call(message)

    return {
        "jsonrpc": "2.0",
        "id": message.get("id"),
        "error": {
            "code": -32601,
            "message": f"Method not found: {method}"
        }
    }


# ============================================================================
# FLASK APPLICATION
# ============================================================================


def create_app() -> Flask:
    """
    Create and configure the Flask application.
    
    Returns:
        Flask: Configured Flask application instance.
    """
    app = Flask(__name__)
    CORS(app)

    @app.route("/mcp", methods=["POST"])
    def mcp_endpoint() -> Response:
        """
        Main MCP endpoint.
        Receives JSON-RPC messages and streams responses via SSE.

        Returns:
            A Flask Response streaming SSE-formatted MCP output.
        """
        message: Dict[str, Any] = request.get_json()

        def generate():
            try:
                response = process_mcp_message(message)
                yield create_sse_message(response)
            except Exception as e:
                logger.error(f"MCP endpoint error: {str(e)}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": f"Parse error: {str(e)}"
                    }
                }
                yield create_sse_message(error_response)

        return Response(generate(), mimetype="text/event-stream")

    @app.route("/health", methods=["GET"])
    def health_check() -> Response:
        """
        Health check endpoint.

        Returns:
            A JSON response indicating server health.
        """
        return jsonify({
            "status": "healthy",
            "server": "customer-management-mcp-server",
            "version": "1.0.0"
        })

    return app


# ============================================================================
# ENTRY POINT
# ============================================================================


if __name__ == "__main__":
    print("Starting MCP Server...")
    print(f"Database: {DB_PATH}")
    print("\nAvailable tools:")
    for tool in MCP_TOOLS:
        print(f"  - {tool['name']}")
    
    app = create_app()
    
    # Setup ngrok if configured
    if USE_NGROK:
        print("\nConfiguring ngrok...")
        ngrok.set_auth_token(NGROK_AUTHTOKEN)
        
        # Kill any existing tunnels on port 10020
        try:
            ngrok.kill()
            print("Cleaned up existing ngrok tunnels")
        except Exception:
            pass  # No existing tunnels, that's fine
        
        try:
            public_url = ngrok.connect(10020)
            print(f"✓ ngrok tunnel established")
            print(f"✓ Public URL: {public_url}")
            print(f"✓ MCP_SERVER_URL: {public_url}/mcp")
        except Exception as e:
            print(f"✗ Failed to setup ngrok: {e}")
            print("Falling back to localhost...")
    else:
        print("\nngrok not configured. Running on localhost only.")
        print("To use ngrok, set NGROK_AUTHTOKEN in your .env file")
    
    print("\nStarting Flask server on 0.0.0.0:10020...")
    app.run(host="0.0.0.0", port=10020, debug=False, use_reloader=False)