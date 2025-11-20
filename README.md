# Multi-Agent Customer Service System

**Assignment: Multi-Agent Customer Service System with A2A and MCP**

This repository houses all of the code and implementation for *Assignment #5: Multi-Agent Customer Service System with A2A and MCP*. This assignment was completed for the Applied Generative AI Agents and Multimodal Intelligence course at The University of Chicago. Specifically, this repository demonstrates coordinated multi-agent task allocation, MCP integration, and A2A protocol implementation using Google's Agent Development Kit (ADK) and A2A SDK.

---

## How to Review This Work

I have modularized all of the code into separate Python modules (`src/config.py`, `src/agents.py`, `src/router.py`, `src/mcp_server.py`). However, to make grading/review convenient, I have provided two equivalent ways to review my implementation:

### Option 1: End-to-End Demo (Recommended for Quick Review)
**File**: `agent_to_agent_demo.ipynb`

This notebook demonstrates the complete A2A system in action:
- Imports and uses all of the the modularized code from `src/`
- Starts the MCP server within the notebook
- Executes all test scenarios
- Shows A2A communication between agents in real-time
- Shows final responses for all of the test queries

The `agent_to_agent_demo.ipynb` is best for a quick review of the system working end-to-end, but since it imports the modularized code from `src/`, all the implementation details (MCP Tool setup, agent initialization, etc.) are hidden in the modules.

### Option 2: Detailed Code Review (Recommended for Full Deep Dive)
**Folder**: `notebooks/`
- **`mcp_server_notebook.ipynb`**: Contains all the code from `src/mcp_server.py` and database configuration via the code cells in the Jupyter notebook
- **`a2a_notebook.ipynb`**: Contains all the code from `src/agents.py`, `src/router.py`, and `src/config.py` via the code cells in the Jupyter notebook

While these notebooks are **identical** to the modularized code in `src/`, they are just presented in notebook format for easier reviewing since every function, class, and implementation detail is visible in executable code cells.

### Assignment Reflection
**File**: `analysis.md`

Lastly, as the per assignment requirements, `analysis.md` contains the 1-2 paragraphs reflection covering:
- Key lessons learned from building this multi-agent system
- Challenges overcome and how I solved them

---

## Project Structure

```
multi-agent-customer-service/
├── README.md                         # This file
├── requirements.txt                  # Python dependencies
├── analysis.md                       # Assignment reflection (lessons learned + challenges)
├── .gitignore                        # Git configuration
├── LICENSE                           # MIT license
├── database_setup.py                 # Database initialization with test data (given)
├── agent_to_agent_demo.ipynb         # End-to-end demo (START HERE!)
│
├── notebooks/                        # Detailed code review
│   ├── mcp_server_notebook.ipynb     # MCP server code in cell format
│   └── a2a_notebook.ipynb            # Agents & router code in cell format
│
└── src/                              # Modularized code
    ├── __init__.py
    ├── config.py                     # Configuration & environment variables
    ├── agents.py                     # Specialist agent definitions (Customer Data + Support)
    ├── mcp_server.py                 # MCP server with the five tools
    └── router.py                     # A2A coordination (RouterOrchestrator + A2AClient)
```

---

## Part 1: System Architecture

This project implements a three-agent system:

### 1. Router Agent (Orchestrator)
- **Location**: `src/router.py` - `RouterOrchestrator`
- **Responsibilities**:
  - Receives customer queries
  - Analyzes query intent using LLM
  - Routes to appropriate specialist agent (customer data or support)
  - Coordinates responses from specialist agents
  - Synthesizes final response
- **Implementation**: Uses Google Gemini to decide which specialist agents to call and how to coordinate them

### 2. Customer Data Agent (Specialist Agent)
- **Location**: `src/agents.py` - `customer_data_agent`
- **Responsibilities**:
  - Accesses customer database via MCP
  - Retrieves customer information
  - Updates customer records
  - Validates data
- **MCP Tools Used**: `get_customer`, `list_customers`, `update_customer`, `create_ticket`, `get_customer_history`

### 3. Support Agent (Specialist Agent)
- **Location**: `src/agents.py` - `support_agent`
- **Responsibilities**:
  - Handles customer support queries
  - Can escalate complex issues
  - Requests customer context from Data Agent
  - Provides solutions and recommendations

### System Architecture Diagram

```
┌──────────────────────────────────────────────────────────┐
│         Router Agent (Orchestrator)                      │
│  - Analyzes user queries                                 │
│  - Routes to appropriate agents                          │
│  - Coordinates multi-agent workflows                     │
└────────────────┬────────────────────┬────────────────────┘
                 │                    │
      ┌──────────▼──────────┐  ┌──────▼──────────────┐
      │ Customer Data Agent │  │  Support Agent      │
      │   (Specialist)      │  │  (Specialist)       │
      │                     │  │                     │
      │ A2A Communication   │  │ A2A Communication   │
      └──────────┬──────────┘  └─────┬───────────────┘
                 │                   │
      ┌──────────▼───────────────────▼──────────┐
      │       MCP Server                        │
      │  - Exposes 5 required tools             │
      │  - Database operations                  │
      │  - SQLite (support.db)                  │
      └─────────────────────────────────────────┘
```

---

## Part 2: MCP Integration

**Location**: `src/mcp_server.py`

Implements a Flask-based MCP server with 5 tools:

### Tools Implemented

1. **get_customer(customer_id)**
   - Retrieves customer record by ID
   - Uses: `customers.id` (primary key)
   - Returns: Full customer details

2. **list_customers(status, limit)**
   - Lists customers filtered by status
   - Uses: `customers.status` ('active' or 'disabled')
   - Returns: List of matching customers

3. **update_customer(customer_id, data)**
   - Updates customer fields
   - Uses: All `customers` fields (name, email, phone, etc.)
   - Returns: Updated customer record

4. **create_ticket(customer_id, issue, priority)**
   - Creates support ticket
   - Uses: `tickets` table fields
   - Returns: New ticket details

5. **get_customer_history(customer_id)**
   - Retrieves all tickets for customer
   - Uses: `tickets.customer_id` (foreign key)
   - Returns: Complete ticket history

### Database Schema

**Customers Table** (created by `database_setup.py`):
```sql
CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    status TEXT CHECK(status IN ('active', 'disabled')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Tickets Table** (created by `database_setup.py`):
```sql
CREATE TABLE tickets (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    issue TEXT NOT NULL,
    status TEXT CHECK(status IN ('open', 'in_progress', 'resolved')),
    priority TEXT CHECK(priority IN ('low', 'medium', 'high')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(customer_id) REFERENCES customers(id)
)
```

### MCP Server Details
- **Framework**: Flask with Server-Sent Events (SSE)
- **Protocol**: JSON-RPC 2.0
- **Public Access**: Ngrok tunnel support (for Google Colab usage)

---

## Part 3: A2A Coordination

**Approach Used**: Lab Notebook Approach (Extended)

My implementation uses the A2A coordination pattern from the provided lab notebook, extended with more complex patterns for routing logic.

### A2ASimpleClient Implementation
**Location**: `src/router.py` - `A2ASimpleClient` class

Handles agent-to-agent HTTP communication:
- Fetches agent card metadata
- Manages agent caching
- Implements proper timeout handling
- Sends messages following A2A SDK pattern

### RouterOrchestrator Coordination
**Location**: `src/router.py` - `RouterOrchestrator` class

Implements intelligent routing:
- Analyzes user intent with LLM
- Decides which agents to call
- Manages agent communication
- Coordinates multi-step workflows

---

## Test Scenarios

All required test scenarios are implemented in the `agent_to_agent_demo.ipynb`:

### Scenario 1: Task Allocation
**Query**: "Get customer information for customer ID 5"

**A2A Flow**:
1. Router Agent receives query
2. Router analyzes: "This requires customer data"
3. Router → Customer Data Agent: "Get customer info for ID 5"
4. Customer Data Agent calls MCP: `get_customer(5)`
5. Customer Data Agent → Router: Returns customer data
6. Router returns final response

**Demonstrated in**: `test_scenario1` cell

### Scenario 2: Negotiation/Escalation
**Query**: "I want to cancel my subscription but I'm having billing issues. My customer ID is 1."

**A2A Flow**:
1. Router detects multiple intents: cancellation + billing issue
2. Router → Customer Data Agent: "Get customer 1 info"
3. Customer Data Agent returns: Customer details + ticket history
4. Router → Support Agent: "Customer wants to cancel but has billing issues"
5. Support Agent → Router: "Create escalation ticket"
6. Router → Customer Data Agent: "Create high-priority ticket"
7. Agents coordinate final response

**Demonstrated in**: `test_scenario2` cell

### Scenario 3: Multi-Step Coordination
**Query**: "Show me the names of all active customers who have closed tickets."

**A2A Flow**:
1. Router decomposes query: "Need customer list + ticket filtering"
2. Router → Customer Data Agent: "List all active customers"
3. Customer Data Agent returns: List of 12 active customers
4. Router → Customer Data Agent: "Get ticket history for IDs: 1,2,3..."
5. Customer Data Agent returns: All tickets for those customers
6. Router filters: Only customers with closed tickets
7. Router synthesizes: List of customer names

**Demonstrated in**: `test_scenario3` cell

---

## Deliverables

### 1. Code Repository (GitHub)
**Location**: https://github.com/bhstoller/multi-agent-customer-service (this repository)

- **MCP Server Implementation**: `src/mcp_server.py`
  - Flask server with 5 required tools
  - Database operations
  - Error handling and logging

- **Agent Implementations**: `src/agents.py`
  - Customer Data Agent (specialist) with MCP integration
  - Support Agent (specialist) with escalation logic
  - Agent cards and instructions

- **Configuration & Deployment**: 
  - `src/config.py`: Centralized configuration
  - `src/router.py`: A2A coordination logic
  - `database_setup.py`: Database initialization
  - `requirements.txt`: All dependencies listed

- **Documentation**:
  - `README.md` (this file): Complete setup and architecture
  - `analysis.md`: Assignment reflection (lessons learned + challenges)

### 2. Colab Notebook
**Location**: `agent_to_agent_demo.ipynb`

**Demonstrates**:
- End-to-end system execution
- 3+ test scenarios with A2A coordination
- Proper output capture showing:
  - User queries
  - Router decision process
  - A2A communication between agents
  - Final responses
- All agents working together
- MCP tool calls visible in output

**Sample Output**:
```
========================================================
 USER QUERY: Get customer information for customer ID 5
========================================================

[ROUTER STEP 1]: The user is asking for information about a specific customer...
   >>> [A2A CALL] Connecting to customer_data at http://localhost:10020...
   <<< [A2A RESPONSE]: Customer details returned...

[ROUTER]: Task Complete.

FINAL RESPONSE:
Customer information for ID 5:
Name: Charlie Brown
Email: charlie.brown@email.com
Phone: +1-555-0105
Status: active
```

---

## Setup & Installation

### Prerequisites
- Python 3.11
- Google API key
- Ngrok token for public URL exposure via Google Colab

### Local Installation

1. **Clone repository:**
   ```bash
   git clone https://github.com/bhstoller/multi-agent-customer-service.git
   cd multi-agent-customer-service
   ```

2. **Create virtual environment:**
   ```bash
      python3 -m venv venv
      source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
      pip install -r requirements.txt
   ```

4. **Create `.env` file:**
   ```
   GOOGLE_API_KEY=your_api_key_here
   MCP_SERVER_URL=http://localhost:10020/mcp
   NGROK_AUTHTOKEN=your_ngrok_token_here
   ```

5. **Initialize database:**
   ```bash
   python database_setup.py
   ```

### Running the System

1. Add to Colab Secrets:
   - `a5-key`: Your Google API key
   - `MCP_SERVER_URL`: Your MCP server URL (via NGrok)

2. Open `agent_to_agent_demo.ipynb` in Google Colab

3. Run all cells sequentially
   - Notebook automatically starts agent servers (ports 10020 and 10021)

---

*Assignment completed: November 2025*
