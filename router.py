"""
Router and A2A Client for Multi-Agent Customer Service System.

This module contains:
- A2ASimpleClient: Handles Agent-to-Agent (A2A) communication via HTTP
- RouterOrchestrator: Orchestrates customer queries by coordinating specialist agents

The Router uses an LLM to reason about queries and decide which agents to call.
"""

import json
import httpx
import google.generativeai as genai
from typing import Any, Dict
from a2a.types import AgentCard, TransportProtocol
from a2a.client import ClientConfig, ClientFactory, create_text_message_object
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH
from config import LLM_MODEL, CUSTOMER_DATA_URL, SUPPORT_URL

# ============================================================================
# A2A CLIENT
# ============================================================================


class A2ASimpleClient:
    """
    A2A client for calling agent servers following the A2A protocol.
    
    Handles HTTP communication with remote agents, manages agent card caching,
    and implements proper timeout and error handling.
    """

    def __init__(self, default_timeout: float = 240.0):
        """
        Initialize the A2A client.
        
        Args:
            default_timeout: Maximum timeout for agent calls in seconds.
        """
        self._agent_info_cache: Dict[str, Dict[str, Any] | None] = {}
        self.default_timeout = default_timeout

    async def create_task(self, agent_url: str, message: str) -> str:
        """
        Send a message to an agent following the official A2A SDK pattern.
        
        Args:
            agent_url: The base URL of the agent server.
            message: The message/query to send to the agent.
            
        Returns:
            str: The text response from the agent.
        """
        # Configure httpx client with timeout
        timeout_config = httpx.Timeout(
            timeout=self.default_timeout,
            connect=10.0,
            read=self.default_timeout,
            write=10.0,
            pool=5.0,
        )

        async with httpx.AsyncClient(timeout=timeout_config) as httpx_client:
            # Check if we have cached agent card data
            if (
                agent_url in self._agent_info_cache
                and self._agent_info_cache[agent_url] is not None
            ):
                agent_card_data = self._agent_info_cache[agent_url]
            else:
                # Fetch the agent card
                agent_card_response = await httpx_client.get(
                    f'{agent_url}{AGENT_CARD_WELL_KNOWN_PATH}'
                )
                agent_card_data = self._agent_info_cache[agent_url] = (
                    agent_card_response.json()
                )

            # Create AgentCard from data
            agent_card = AgentCard(**agent_card_data)

            # Create A2A client with the agent card
            config = ClientConfig(
                httpx_client=httpx_client,
                supported_transports=[
                    TransportProtocol.jsonrpc,
                    TransportProtocol.http_json,
                ],
                use_client_preference=True,
            )

            factory = ClientFactory(config)
            client = factory.create(agent_card)

            # Create the message object
            message_obj = create_text_message_object(content=message)

            # Send the message and collect responses
            responses = []
            async for response in client.send_message(message_obj):
                responses.append(response)

            # The response is a tuple - get the first element (Task object)
            if (
                responses
                and isinstance(responses[0], tuple)
                and len(responses[0]) > 0
            ):
                task = responses[0][0]  # First element of the tuple

                # Extract text: task.artifacts[0].parts[0].root.text
                try:
                    return task.artifacts[0].parts[0].root.text
                except (AttributeError, IndexError):
                    return str(task)

            return 'No response received'


# ============================================================================
# ROUTER ORCHESTRATOR
# ============================================================================


class RouterOrchestrator:
    """
    Router agent that orchestrates customer service by coordinating specialist agents.
    
    Uses an LLM to analyze queries, decide which agents to call, and synthesize responses.
    """

    def __init__(self, a2a_client: A2ASimpleClient):
        """
        Initialize the Router Orchestrator.
        
        Args:
            a2a_client: An A2ASimpleClient instance for agent communication.
        """
        self.client = a2a_client
        # Using the high-reasoning model for the "Brain"
        self.model = genai.GenerativeModel(LLM_MODEL)
        
        # URLs for your running agents
        self.DATA_AGENT_URL = CUSTOMER_DATA_URL
        self.SUPPORT_AGENT_URL = SUPPORT_URL

    async def call_agent(self, agent_name: str, query: str) -> str:
        """
        Execute an A2A call to a specialist agent.
        
        Args:
            agent_name: Name of the agent ("customer_data" or "support_agent").
            query: The query/message to send to the agent.
            
        Returns:
            str: The agent's response.
        """
        url = self.DATA_AGENT_URL if agent_name == "customer_data" else self.SUPPORT_AGENT_URL
        print(f"   >>> [A2A CALL] Connecting to {agent_name} at {url}...")
        
        try:
            # Use the existing a2a_client logic
            response = await self.client.create_task(url, query)
            return response
        except Exception as e:
            return f"Error calling agent: {str(e)}"

    async def process_query(self, user_query: str) -> str:
        """
        Process a customer query by coordinating specialist agents.
        
        Uses the LLM to reason about the query, decide which agents to call,
        and synthesize a final response.
        
        Args:
            user_query: The customer's query/request.
            
        Returns:
            str: The final response to the customer.
        """
        # --- FORMATTING OUTPUT ---
        header_text = f" USER QUERY: {user_query} "
        separator = "=" * len(header_text)
        
        print(f"\n{separator}")
        print(header_text)
        print(f"{separator}")
        # --- END FORMATTING ---
        
        max_turns = 15
        
        # System prompt defines the Router's logic
        system_prompt = """
You are the Router Agent (Orchestrator) for a customer service system. 
You have two specialized sub-agents you can call via A2A tools:

1. "customer_data" 
   - Capabilities: Get customer details, list customers, update records, get ticket history, create tickets.
   
2. "support_agent" 
   - Capabilities: General support advice, troubleshooting, escalation decisions.

Your Goal: Answer the user's request by coordinating these agents.

CRITICAL INSTRUCTION FOR LISTS: 
- If the user asks for a list of customers with specific conditions (e.g., "active customers with open tickets"), do NOT check them one by one. 
- **BATCH YOUR REQUESTS:**
  1. Call customer_data to list active customers.
  2. Send a **SINGLE** message to customer_data requesting ticket history for **ALL** the retrieved customer IDs at once (e.g. "Get history for customer IDs 4, 5, 8, 10..."). 
  3. Filter the results yourself based on the returned data.

RESPONSE FORMAT:
You must strictly return a JSON object in this format (no markdown formatting):
{
    "thought": "Explanation of your reasoning",
    "action": "call_agent" OR "final_answer",
    "agent_name": "customer_data" OR "support_agent" (only if action is call_agent),
    "content": "The specific query string to send to that agent" OR "The final text response to the user"
}
"""

        messages = [
            {"role": "user", "parts": [system_prompt + f"\n\nUser Query: {user_query}"]}
        ]

        for i in range(max_turns):
            try:
                response = await self.model.generate_content_async(messages)
                response_text = response.text
            except Exception as e:
                print(f"[ROUTER ERROR]: Gemini generation failed: {e}")
                return "System Error"
            
            # Clean up JSON
            clean_text = response_text.replace("```json", "").replace("```", "").strip()
            
            try:
                plan = json.loads(clean_text)
            except json.JSONDecodeError:
                print(f"[ROUTER ERROR]: Could not parse JSON plan. Raw: {clean_text}")
                messages.append({"role": "user", "parts": ["Invalid JSON. Please return ONLY valid JSON."]})
                continue

            print(f"\n[ROUTER STEP {i+1}]: {plan['thought']}")

            if plan['action'] == "final_answer":
                print(f"\n[ROUTER]: Task Complete.")
                return plan['content']
            
            elif plan['action'] == "call_agent":
                # Execute A2A Call
                agent_response = await self.call_agent(plan['agent_name'], plan['content'])
                
                snippet = str(agent_response)[:200].replace('\n', ' ')
                print(f"   <<< [A2A RESPONSE]: {snippet}...")
                
                # Add context to history
                messages.append({"role": "model", "parts": [clean_text]})
                messages.append({"role": "user", "parts": [f"Result from {plan['agent_name']}: {agent_response}"]})

        return "Error: Maximum turns reached without final answer."