# Conclusion and Analysis

## What I Learned

1. **Agent Coordination Requires Explicit Communication Protocols**: From this assignment, one of the main things I learned was that managing state and information flow between multiple agents is significantly more complex than a single agent. Without explicit logging at every coordination point and clear communication protocols between agents, debugging multi-agent systems was very difficult to do. While the A2A pattern provides good default instructions, the orchestrator had to be really strong in order to manage the conversation effectively.

2. **MCP as a Critical Interface Layer**: I learned fairly early on into the assignment that the entire system relied on the MCP server, which had to be working for everyhting else to work as well. Specifically, proper tool definition, and timeout configurations were missing in my early attempts, which caused silent failures to cascade through my system. Thus, I learned that MCP tools need to be very well-defined with very clear error messages for debugging.

3. **LLM-Powered Routing Demands Careful Prompt Engineering**: I also learned how helpful LLM tools are for helping decide which agents to call. Specifically, I found that LLMs responded well to structure (ie my prompt/instructions) and were therefore able to list available agents, provide clear decision criteria, and specify the output format. Before using the LLM (and a set of instructions), my first router would sometimes make different decisions for the same query.

## Challenges Overcome

1. **Understanding the Router's Architecture**: The biggest challenge that I had to overcome was initially implementing the router as a `SequentialAgent`. However, I ultimately realized that this configuration wasn't the right approach, especially since it could not be given any instructions (prompting). However, I was able to solve this by switching to a `RouterOrchestrator` (a custom python class) with Gemini LLM for reasoning and `A2ASimpleClient` for agent communicationm, which ended up being clearer and more flexible than having the router be a specialist agent.

2. **A2A Communication and Message Passing**: When starting the assignment, the A2A SDK's HTTP communication pattern wasn't very intuitive, and in my early attempts, I kept seeing my system fail silently or crash due to timeout misconfigurations. I ultimately solved this by building a more robust `A2ASimpleClient` with proper timeout configurations and agent card caching. Together, with explicit logging instructions, I was able to make debugging much easier.

3. **State Management Across Agents**: Lastly, tracking information flow between my specialist agents and ensuring that each of them had the necessary context for decisions was another big challenge early on. Specifically, my agents initially would lose track of information like customer IDs or forget to pass results between agents. However, I solved this by maintaining message history via the router (I required that all messages sent to Gemini included responses) and (again) adding logging at every coordination point.

## Generative AI (LLM) Usage: Queries and Prompts
For my project, I made a few major queries to Claude to help me with my assigment. Please see the queries and answers below:

### 1. Repository Organization

**Prompt:**
<br>

> I'm building a multi-agent customer service system for an assignment. The system has three main parts:
> - Part 1: Three specialized agents - a Router/Orchestrator agent and two specialist agents (Customer Data Agent and Support Agent), each with detailed system instructions
> - Part 2: An MCP server with 5 database tools (get_customer, list_customers, update_customer, create_ticket, get_customer_history) that the specialist agents (specifically the customer data agent) will call
> - Part 3: A2A (agent-to-agent) protocol for coordination between the router and specialist agents
>
> I already have two notebooks (mcp_server.ipynb and agent_to_agent.ipynb) that have all of my code to implement this. However, I Ultimately need to submit this as both a Google Colab notebook and as modularized Python code. 
>
> What would be the best way to organize this GitHub repository so that:
> 1. It's clear to a TA what I did on the assignment
> 2. The code is easy to understand
> 3. It's professionally structured and meets best practices
> 4. The modularization is clear but the demo is still understandable
>
> I am thinking of separating the code in those two notebooks into python scripts (maybe agents, router, and mcp)?
> What repo structure do you recommend?

**Response:**
<br>
Certainly! I would recommend organizing the repository as follows:
1. Create a `src/` folder containing modularized Python modules: `config.py`, `agents.py`, `mcp_server.py`, and `router.py`
2. Keep your `agent_to_agent_demo.ipynb` at the root as the primary demonstration notebook
3. Create a `notebooks/` folder with reference notebooks (`mcp_server_notebook.ipynb` and `agent_to_agent_notebook.ipynb`) that display the same code in Jupyter notebook cell format for easy review during grading
4. Include `README.md`, `requirements.txt` at the root level

**Why this works:**
This structure clearly separates production code (`src/`) from demonstration and reference materials (`notebooks/` and demo notebook). The approach makes it obvious that the system can be both reviewed as a working demo and inspected at the code level!

This is the exact structure I implemented and is reflected in my final repository.

### 2. Router Agent Architecture

**Prompt:**
> Im working on an assignment to build a multi-agent customer service system that has three main parts:
> - Part 1: Three specialized agents - a Router/Orchestrator agent and two specialist agents (Customer Data Agent and Support Agent), each with detailed system instructions
> - Part 2: An MCP server with 5 database tools (get_customer, list_customers, update_customer, create_ticket, get_customer_history) that the specialist agents (specifically the customer data agent) will call
> - Part 3: A2A (agent-to-agent) protocol for coordination between the router and specialist agents
> 
> Specifically, I need your help building the Router agent part of the A2A system. Here's what I need it to do:
> - Receives a customer query as input
> - Analyzes the query to understand what the user is asking
> - Decides whether to call the Customer Data Agent for data questions, the Support Agent for support/general LLM questions (or both)
> - Handle "complex queries that require multiple agent calls"
> - Coordinate and synthesize responses from multiple agents
>
> Right now, I already have built the two specialist agents via Google ADK Agents:
> - **Customer Data Agent**: Calls my MCP tools (listed above) to get/update customer data and return it in JSON format
> - **Support Agent**: Handles general support questions and skips the requrest if it is a data request to defer to my Customer Data Agent
>
> The TA suggested that I implement this as a custom class rather than using Google ADK's SequentialAgent (which I am currently doing) and via an A2A Simple Client (code seen below). 

    Class A2ASimpleClient:
    """A2A Simple to call A2A servers."""

    def __init__(self, default_timeout: float = 240.0):
        self._agent_info_cache: dict[
            str, dict[str, Any] | None
        ] = {}  # Cache for agent metadata
        self.default_timeout = default_timeout

    async def create_task(self, agent_url: str, message: str) -> str:
        """Send a message following the official A2A SDK pattern."""
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

> 
> Can you help me design a custom class that would make this router work effectively?

**Response:**
<br>

You can do this by creating a `RouterOrchestrator` class with the following architecture:
- Constructor takes your `A2ASimpleClient` instance as a parameter for agent communication
- Uses Google Gemini as the decision-making engine (via `genai.GenerativeModel`)
- Implements an `async def process_query(user_query)` method that:
  - Runs a reasoning loop (maximum 15 turns)
  - At each turn, sends the current state to Gemini and expects JSON output
  - JSON format: `{"thought": "reasoning", "action": "call_agent" or "final_answer", "agent_name": "customer_data" or "support_agent", "content": "query or response"}`
  - Maintains message history to give Gemini context from previous agent calls
  - Breaks when action is "final_answer" and returns that content
- Implements an `async def call_agent(agent_name, query)` method that:
  - Uses A2ASimpleClient to make HTTP calls to the specialist agent URLs
  - Handles errors gracefully
  - Returns the agent's response to add back to the message history
- The class effectively implements an "agentic loop" where an LLM reasons about what to do, takes actions (agent calls), observes results, and repeats until it reaches a final answer

Do you want me to share code for how to implement this in your assignment?

This design is exactly what I implemented in `src/router.py` as the `RouterOrchestrator` class.

### 3. Code Modularization

**Prompt:**
> I'm building a multi-agent customer service system for an assignment. The system has three main parts:
> - Part 1: Three specialized agents - a Router/Orchestrator agent and two specialist agents (Customer Data Agent and Support Agent), each with detailed system instructions
> - Part 2: An MCP server with 5 database tools (get_customer, list_customers, update_customer, create_ticket, get_customer_history) that the specialist agents (specifically the customer data agent) will call
> - Part 3: A2A (agent-to-agent) protocol for coordination between the router and specialist agents
>
> Right now I have two Jupyter notebooks with all my code to complete the assignment instructions above. However, I want to modularize this into individual separate Python scripts while keeping my code/my approach exaclty the same. I have attached both notebooks to this prompt. Specifically, 
>
> **mcp_server_notebook.ipynb** contains:
> - Database connection helpers (get_db_connection, row_to_dict)
> - Five MCP tool implementations (get_customer, list_customers, update_customer, create_ticket, get_customer_history)
> - MCP message handlers (handle_initialize, handle_tools_list, handle_tools_call, process_mcp_message)
> - Flask app creation and SSE (Server-Sent Events) endpoint setup
>
> **agent_to_agent_notebook.ipynb** contains:
> - Configuration variables and environment setup
> - Customer Data Agent definition (with MCP toolset) and agent card
> - Support Agent definition and agent card
> - Router Agent instruction (system prompt)
> - A2ASimpleClient class for HTTP agent-to-agent communication
> - RouterOrchestrator class for orchestration logic
>
> I am thinking of separating the code in those two notebooks 
> into python scripts (agents.py, router.py, and mcp_server.py)
>
> Can you please split up my code from the notebooks into these modularized code files?

**Response:**
<br>
Certainly! I will create three different python files that use your code exactly from `mcp_server_notebook.ipynb` and `agent_to_agent_notebook.ipynb`. Here is what they will all entail:

- **mcp_server.py**: Complete MCP server implementation (database helpers, all 5 tools, message handlers, Flask app creation, and `if __name__ == "__main__"` entry point for running the server)
- **agents.py**: All agent definitions (customer_data_agent and customer_data_agent_card, support_agent and support_agent_card, agent instructions including ROUTER_AGENT_INSTRUCTION, plus `__all__` exports for easy importing)
- **router.py**: All coordination logic (A2ASimpleClient class for A2A communication, RouterOrchestrator class for query orchestration)

This modularization follows the single-responsibility principle:
- `config.py` handles all environment/configuration concerns
- `mcp_server.py` is self-contained and can run standalone
- `agents.py` is purely definitions and instructions
- `router.py` contains the orchestration logic

Each module can be imported independently and the code is identical to what was in the notebooks, just reorganized.

Perfect! Here's the updated version with actual detailed prompts:

config.py
mcp_server.py
agents.py
router.py

Ultimately, I used these files as a starting point, and applied my own custom formatting/styling, as well as fixing errors to make sure they worked together. Then I called them all via agent_to_agent_demo.ipynb.

### 4. Specialist Agent Instructions

**Prompt:**
<br>

> I'm building a multi-agent customer service system for an assignment. The system has three main parts:
> - Part 1: Three specialized agents - a Router/Orchestrator agent and two specialist agents (Customer Data Agent and Support Agent), each with detailed system instructions
> - Part 2: An MCP server with 5 database tools (get_customer, list_customers, update_customer, create_ticket, get_customer_history) that the specialist agents (specifically the customer data agent) will call
> - Part 3: A2A (agent-to-agent) protocol for coordination between the router and specialist agents
>
> I need to write system instructions for two specialist agents that will work together in my system. Here is what I want each of the agents to do
>
> **Customer Data Agent:**
> - Use the MCP tools listed above to answer questions
> - The mcp tools are get_customer(id), list_customers(status), update_customer(id, data), create_ticket(id, issue, priority), get_customer_history(id)
> - Never create any new data (right now it sometimes makes new things up)
> - Handle errors without crashing by sharing when something goes wrong
> - Retain inforamtion when passing along and add timestamps to data added
>
> **Support Agent:**
> - Answer classic customer support questions
> - Know when a query is actually asking for data/information and refuse to answer it if it is a data question for the customer data agent
> - Ask for inforamtion from the customer data agent from the router when it's needed for a support decision
> - Format answers in real wording not JSON
>
> My Router uses an LLM to reason step-by-step about which agent to call, where it requests the same structured response every time.
>
> Can you help me write clear instructions for my two agents that will work well in this system and with my router?

**Response:**
<br>
Absolutely, writing prompts is one of the most important parts of an agentic system like you are building. Here are two prompts you can use for the instructions for your agents:

**Customer Data Agent Instruction:**
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

**Support Agent Instruction:**
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

These instructions provide:
- Clear behavioral constraints (what each agent should/shouldn't do)
- Explicit logging that makes router debugging easy
- Structured responses that the router can parse
- Clear decision criteria (how to distinguish data requests from support requests)

As seen in my implementation, these are very similar to the prompts I used for both of my agents since they were very effective.

## 5. README Documentation

**Prompt:**
> I'm building a multi-agent customer service system for an assignment. The system has three main parts:
> - Part 1: Three specialized agents - a Router/Orchestrator agent and two specialist agents (Customer Data Agent and Support Agent), each with detailed system instructions
> - Part 2: An MCP server with 5 database tools (get_customer, list_customers, update_customer, create_ticket, get_customer_history) that the specialist agents (specifically the customer data agent) will call
> - Part 3: A2A (agent-to-agent) protocol for coordination between the router and specialist agents
> 
> I have fully completed the code for the assignment, but now I need to write a README to include with my github repo. Specifically, I want the README to mention that:
>
> - I have modularized the code in `src/` (config.py, agents.py, mcp_server.py, router.py) and call it in a working demonstration in `agent_to_agent_demo.ipynb` that imports and  that code. However, I also created two notebooks in the `notebooks/` folder (mcp_server_notebook.ipynb and agent_to_agent_notebook.ipynb) that show the exact same code as the modularized code, but in the format of Jupyter notebooks (code cell format) instead. I did this only for grading convenience so that my TA can easily see all of the steps I took that might be hidden from my modularized end to end implimentation in agent_to_agent_demo.ipynb
> - The system architecture has three agents (Router orchestrator, Customer Data specialist, Support specialist)
> - The MCP server exposes 5 database tools
> - I used A2A coordination for agent communication
> - There are test scenarios demonstrating multi-agent coordination
> - I also need to mention the database schema:
>   CREATE TABLE customers (
>    id INTEGER PRIMARY KEY,
>    name TEXT NOT NULL,
>    email TEXT,
>    phone TEXT,
>    status TEXT CHECK(status IN ('active', 'disabled')),
>    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
>    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
>    )
>
>   CREATE TABLE tickets (
>    id INTEGER PRIMARY KEY,
>    customer_id INTEGER NOT NULL,
>    issue TEXT NOT NULL,
>    status TEXT CHECK(status IN ('open', 'in_progress', 'resolved')),
>    priority TEXT CHECK(priority IN ('low', 'medium', 'high')),
>    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
>    FOREIGN KEY(customer_id) REFERENCES customers(id)
>   )
> - I also need to mention the setup and installation instructions where you can use my requirements.txt file to create a venv for usage of my system
>
> Can you write me a README that touches on all these things?

**Response:**
Absolulutely, I can definitely write a README about your project. Regarding the opening section, I will make sure to immediately clarify that code is modularized in `src/`, but explain that there are two options for viewing:

- Option 1: Run `agent_to_agent_demo.ipynb` for end-to-end demo (imports modularized code, starts MCP server, executes test scenarios)
- Option 2: Review `notebooks/` for detailed code inspection (same code in notebook cell format for easier grading)

I will be sure to explicitly state that both approaches show identical implementation and the notebooks exist purely for grading convenience.


Here's the updated version of your README that touches on how to view your project, the project structure, technical sections, and key principles.

Ultimately, I used this as a first draft for my README and made a number of changes on top of it. However, it was really helpful to have such a strong and thorough starting point (including a cool diagram), that made it really easy to update.