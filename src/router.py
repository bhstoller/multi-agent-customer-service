"""
This module contains the implementation logic for the Router agent, where the router uses an LLM
to respond to queries and decide which agents to call. Specifically, it includes:
- A2ASimpleClient: Handles the A2A communication via HTTP
- RouterOrchestrator: Orchestrates customer queries by coordinating specialist agents (via custom class)
"""

# Imports
import json
import httpx
import google.generativeai as genai
from typing import Any, Dict
from a2a.types import AgentCard, TransportProtocol
from a2a.client import ClientConfig, ClientFactory, create_text_message_object
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH
from config import LLM_MODEL, CUSTOMER_DATA_URL, SUPPORT_URL

# ======================================================================================
# A2A CLIENT
# ======================================================================================
# The A2A client handles communication with remote agents via HTTP. The code is exactly 
# the same as the code provided in the hands on labs from class.

class A2ASimpleClient:
    """A2A Simple to call A2A servers."""

    def __init__(self, default_timeout: float = 240.0):
        self._agent_info_cache: Dict[
            str, Dict[str, Any] | None
        ] = {} # Cache for agent metadata
        self.default_timeout = default_timeout

    async def create_task(self, agent_url: str, message: str) -> str:
        """Send a message following the official A2A SDK pattern."""
        # Configure httpx client with timeout
        timeout_config = httpx.Timeout(
            timeout= self.default_timeout,
            connect= 10.0,
            read= self.default_timeout,
            write= 10.0,
            pool= 5.0,
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
                httpx_client= httpx_client,
                supported_transports= [
                    TransportProtocol.jsonrpc,
                    TransportProtocol.http_json,
                ],
                use_client_preference= True,
            )

            factory = ClientFactory(config)
            client = factory.create(agent_card)

            # Create the message object
            message_obj = create_text_message_object(content= message)

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
# This is a custom class that I built to implement the Router agent logic.
# The router uses an LLM to analyze user queries, decide whether to call the 
# customer data agent or support agent (or both), and synthesize the result.

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
        self.model = genai.GenerativeModel(LLM_MODEL)
        
        # URLs for the specialist agents
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
        print(f"    >>> [A2A CALL] Connecting to {agent_name} at {url}...")
        
        try:
            # Use the existing a2a_client logic
            response = await self.client.create_task(url, query)
            return response
        except Exception as e:
            return f"Error calling agent: {str(e)}"

    async def process_query(self, user_query: str) -> str:
        """
        Process a customer query by coordinating specialist agents, by using the LLM to 
        reason about the query, decide which agents to call, and form the final response.
        
        Args:
            user_query: The customer's query/request.
            
        Returns:
            str: The final response to the customer.
        """

        # Format the output by having === bars the length of the query
        header_text = f" USER QUERY: {user_query} "
        separator = "=" * len(header_text)
        
        print(f"\n{separator}")
        print(header_text)
        print(f"{separator}")
        
        # Set the maximum nunber of reasoning turns
        max_turns = 15
        
        # Define the Router's logic via detailed instructions
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

        # Loop through reasoning turns, using try/except to handle any errors
        for i in range(max_turns):
            try:
                response = await self.model.generate_content_async(messages)
                response_text = response.text
            except Exception as e:
                print(f"[ROUTER ERROR]: Gemini generation failed: {e}")
                return "System Error"
            
            # Clean up the JSON response
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