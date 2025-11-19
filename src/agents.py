"""
This module contains all of the agent configurations, instructions, and agent cards
for the three specialized agents in the system:
- Customer Data Agent: Handles all customer data requests via the MCP Server Tools
- Support Agent: Handles all customer support and escalation requests
- Router (Orchestrator): Facilitates the communication between customer data and support agents (runs as client, not server)
"""

# Imports
import os
from google.adk.agents import Agent
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams
from a2a.types import (
    AgentCard,
    AgentCapabilities,
    AgentSkill,
    TransportProtocol,
)
from config import MCP_SERVER_URL, LLM_MODEL

# ======================================================================================
# CUSTOMER DATA AGENT
# ======================================================================================
# The customer data agent connects directly with the MCP server to handle all
# data operations including information retrieval, updates, and ticket creation
CUSTOMER_DATA_AGENT_URL = "http://127.0.0.1:10020"

CUSTOMER_DATA_AGENT_INSTRUCTION = """
You are the Customer Data Agent.

IMPORTANT LOGGING: Begin EVERY response with:
[CUSTOMER_DATA_AGENT]: <brief description of what you're doing>

Your role is to interface with the MCP server and perform EXACT data operations.

REQUIRED RULES:
- ALWAYS announce your action first: [CUSTOMER_DATA_AGENT]: Calling get_customer for ID X
- ALWAYS call an MCP tool for any operation involving customer data.
- NEVER invent fields, values, or IDs.
- ALWAYS return valid JSON after your announcement.
- If a customer does not exist, return:
  {"error": "Customer ID not found", "customer_id": <id>}
- For successful lookups, return:
  {"customer": { ...mcp result... }}

AVAILABLE OPERATIONS:
- get_customer(customer_id)
- list_customers(status, limit)
- update_customer(customer_id, data)
- create_ticket(customer_id, issue, priority)
- get_customer_history(customer_id)

ADDITIONAL RULES:
- When updating a customer, preserve any fields that are not being modified.
- When creating a ticket, always include created_at returned by MCP.
- When listing customers, return an array of customer objects.

ALWAYS start with [CUSTOMER_DATA_AGENT]: then provide JSON.
"""

customer_data_agent = Agent(
    model= LLM_MODEL,
    name= "customer_data_agent",
    tools= [
        MCPToolset(
            connection_params= StreamableHTTPConnectionParams(url= MCP_SERVER_URL)
        )
    ],
    instruction= CUSTOMER_DATA_AGENT_INSTRUCTION,
)

customer_data_agent_card = AgentCard(
    name= "Customer Data Agent",
    url= CUSTOMER_DATA_AGENT_URL,
    description= "Fetches and updates customer data using MCP tools",
    version= "1.0",
    capabilities= AgentCapabilities(streaming=False),
    default_input_modes= ["text/plain"],
    default_output_modes= ["application/json"],
    preferred_transport= TransportProtocol.jsonrpc,
    skills= [
        AgentSkill(
            id= "customer_data_access",
            name= "Customer Data Access",
            description= "Retrieve and update customer records",
            tags= ["customer", "data", "database", "lookup"],
            examples= [
                "Get customer 42",
                "Update customer 5 email",
                "Show all customers",
            ],
        )
    ],
)

# ======================================================================================
# SUPPORT AGENT
# ======================================================================================
# The support agent handles customer support queries, troubleshooting, and escalations.
# It can request customer context from the Router when needed for support tasks.
SUPPORT_AGENT_URL = "http://127.0.0.1:10021"

SUPPORT_AGENT_INSTRUCTION = """
You are the Support Agent.

IMPORTANT LOGGING: Begin EVERY response with:
[SUPPORT_AGENT]: <brief description of what you're doing>

CRITICAL RULE: If the user asks for customer INFORMATION/DATA (get, retrieve, show, lookup),
you MUST respond with:

[SUPPORT_AGENT]: This is a data retrieval request, not a support question.
PASS_TO_CUSTOMER_DATA_AGENT

Only handle SUPPORT questions like:
- "How do I reset my password?"
- "I need help with my account"
- "I'm having trouble logging in"

If the query is asking for customer data/information/records, say:
[SUPPORT_AGENT]: PASS_TO_CUSTOMER_DATA_AGENT

If customer-specific data is required for a SUPPORT question, respond with:
[SUPPORT_AGENT]: Requesting customer data from router
{
  "needs_customer_data": true,
  "reason": "<why>",
  "requested_fields": ["email", "tickets", "status", ...]
}

When the Router provides customer data for a support question:
- Announce: [SUPPORT_AGENT]: Processing support request with customer context
- Use only those fields
- Provide a natural-language support answer

Your job: troubleshooting, escalation, and answering support questions ONLY.
For data retrieval queries, defer to customer data agent.

ALWAYS start responses with [SUPPORT_AGENT]:
"""

support_agent = Agent(
    model=LLM_MODEL,
    name="support_agent",
    instruction=SUPPORT_AGENT_INSTRUCTION,
)

support_agent_card = AgentCard(
    name= "Support Agent",
    url= SUPPORT_AGENT_URL,
    description= "Handles general support questions and escalates to customer data agent when needed",
    version= "1.0",
    capabilities= AgentCapabilities(streaming= True),
    default_input_modes= ["text/plain"],
    default_output_modes= ["text/plain"],
    preferred_transport= TransportProtocol.jsonrpc,
    skills= [
        AgentSkill(
            id= "customer_support",
            name= "Customer Support",
            description= "Provides general support responses",
            tags= ["support", "help", "troubleshooting"],
            examples= [
                "How do I reset my password?",
                "What is your refund policy?",
                "I need help with my account.",
            ],
        )
    ],
)

# ======================================================================================
# ROUTER AGENT (Orchestrator)
# ======================================================================================
# The Router agent doesn't run as an A2A server. Instead it is an orchestrator that
# analyzes user queries and makes A2A calls to the specialist agents.

ROUTER_AGENT_INSTRUCTION = """
You are the Router Agent - the orchestrator of the customer service system.

IMPORTANT LOGGING: Begin EVERY response with:
[ROUTER STEP X]: <what you're doing>

Your role is to:
1. Understand the user's intent
2. Decompose complex queries into sub-tasks
3. Delegate to specialized agents (Customer Data Agent, Support Agent)
4. Coordinate responses from multiple agents
5. Synthesize a final answer

AVAILABLE AGENTS:
- Customer Data Agent: For all customer data retrieval, updates, tickets
- Support Agent: For support questions, troubleshooting, escalations

DECISION LOGIC:
- If the query is about customer DATA → Customer Data Agent
- If the query is about SUPPORT → Support Agent
- If the query has BOTH → Coordinate between agents
- Complex queries may need multiple agent calls and negotiation

Always think step-by-step and announce each step with [ROUTER STEP X]:

ALWAYS start responses with [ROUTER STEP 1]:
"""

# NOTE: The router is not instantiated here because it doesn't run as an A2A server.
# The RouterOrchestrator class is defined the actual notebook where it called (agent_to_agent_demo.ipynb)


# ======================================================================================
# Module Export Shortcut
# ======================================================================================

# Setting a designation of all for easy importation of all the agents
__all__ = [
    "customer_data_agent",
    "customer_data_agent_card",
    "support_agent",
    "support_agent_card",
    "CUSTOMER_DATA_AGENT_INSTRUCTION",
    "SUPPORT_AGENT_INSTRUCTION",
    "ROUTER_AGENT_INSTRUCTION",
]


if __name__ == "__main__":
    # Confirm agent creation
    print("Customer_data_agent created")
    print("Customer_data_agent_card created")
    print("Support_agent created")
    print("Support_agent_card created")
    print("\nAll agents from the agents module loaded successfully!")