# Multi-Agent Customer Service System

A production-ready multi-agent customer service system demonstrating coordinated task allocation, MCP (Model Context Protocol) integration, and Agent-to-Agent (A2A) communication using Google's Agent Development Kit (ADK) and A2A SDK.

Built for The University of Chicago's Applied Generative AI Agents and Multimodal Intelligence course.

---

## Overview

This repository demonstrates a sophisticated multi-agent architecture where specialized AI agents coordinate to handle complex customer service queries. The system features intelligent routing, database access through MCP tools, and seamless agent-to-agent communication.

### Key Features

- **Intelligent Routing**: LLM-powered query analysis and task delegation
- **MCP Integration**: Five database tools for customer data management
- **A2A Protocol**: Coordinated multi-agent workflows with HTTP-based communication
- **Modular Architecture**: Clean separation of concerns with reusable components
- **End-to-End Demo**: Complete working examples with multiple test scenarios

---

## Quick Start

### Explore the System

**Option 1: End-to-End Demo** (Recommended)  
**File**: [agent_to_agent_demo.ipynb](agent_to_agent_demo.ipynb)

This notebook demonstrates the complete A2A system in action:
- Imports modularized code from `src/`
- Starts the MCP server within the notebook
- Executes multiple test scenarios
- Shows A2A communication between agents in real-time
- Displays final responses for all test queries

**Option 2: Detailed Implementation Review**  
**Folder**: `notebooks/`
- [mcp_server_notebook.ipynb](mcp_server_notebook.ipynb): MCP server implementation with database configuration
- [a2a_notebook.ipynb](a2a_notebook.ipynb): Agent definitions, router logic, and configuration

These notebooks present the same implementation in executable code cells for easier reviewing.

### Reflection
**File**: [conclusion.md](conclusion.md)

Key lessons learned from building this multi-agent system and challenges overcome during implementation.

---

## Project Structure

```
multi-agent-customer-service/
├── README.md                         # This file
├── requirements.txt                  # Python dependencies
├── conclusion.md                     # Implementation reflection
├── .gitignore                        # Git configuration
├── LICENSE                           # MIT license
├── database_setup.py                 # Database initialization with test data
├── agent_to_agent_demo.ipynb         # End-to-end demo (START HERE!)
│
├── notebooks/                        # Detailed implementation notebooks
│   ├── mcp_server_notebook.ipynb     # MCP server code
│   └── a2a_notebook.ipynb            # Agents & router code
│
└── src/                              # Modularized code
    ├── __init__.py
    ├── config.py                     # Configuration & environment variables
    ├── agents.py                     # Specialist agent definitions
    ├── mcp_server.py                 # MCP server with five tools
    └── router.py                     # A2A coordination logic
```

---

## System Architecture

This project implements a three-agent system with specialized roles:

### 1. Router Agent (Orchestrator)
- **Location**: [`src/router.py`](src/router.py) - `RouterOrchestrator`
- **Responsibilities**:
  - Receives customer queries
  - Analyzes query intent using LLM
  - Routes to appropriate specialist agents
  - Coordinates responses from multiple agents
  - Synthesizes final responses
- **Implementation**: Uses Google Gemini for intelligent routing decisions

### 2. Customer Data Agent (Specialist)
- **Location**: [`src/agents.py`](src/agents.py) - `customer_data_agent`
- **Responsibilities**:
  - Accesses customer database via MCP
  - Retrieves and updates customer information
  - Manages support tickets
  - Validates data integrity
- **MCP Tools**: `get_customer`, `list_customers`, `update_customer`, `create_ticket`, `get_customer_history`

### 3. Support Agent (Specialist)
- **Location**: [`src/agents.py`](src/agents.py) - `support_agent`
- **Responsibilities**:
  - Handles customer support queries
  - Escalates complex issues
  - Requests customer context from Data Agent
  - Provides solutions and recommendations

### Architecture Diagram

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
      │  - Exposes 5 database tools             │
      │  - Database operations                  │
      │  - SQLite (support.db)                  │
      └─────────────────────────────────────────┘
```

---

## MCP Integration

**Location**: [`src/mcp_server.py`](src/mcp_server.py)

A Flask-based MCP server implementing the Model Context Protocol with five database tools:

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

**Customers Table**:
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

**Tickets Table**:
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

### Server Details
- **Framework**: Flask with Server-Sent Events (SSE)
- **Protocol**: JSON-RPC 2.0
- **Public Access**: Ngrok tunnel support for cloud deployment

---

## A2A Coordination

### A2ASimpleClient Implementation
**Location**: [`src/router.py`](src/router.py) - `A2ASimpleClient` class

Handles agent-to-agent HTTP communication:
- Fetches agent card metadata
- Manages agent caching
- Implements timeout handling
- Sends messages following A2A SDK protocol

### RouterOrchestrator Coordination
**Location**: [`src/router.py`](src/router.py) - `RouterOrchestrator` class

Implements intelligent routing logic:
- Analyzes user intent with LLM
- Decides which agents to call
- Manages agent communication
- Coordinates multi-step workflows

---

## Example Scenarios

All scenarios are implemented in [`agent_to_agent_demo.ipynb`](agent_to_agent_demo.ipynb):

### Scenario 1: Simple Task Allocation
**Query**: "Get customer information for customer ID 5"

**A2A Flow**:
1. Router receives query
2. Router analyzes: "This requires customer data"
3. Router → Customer Data Agent: "Get customer info for ID 5"
4. Customer Data Agent calls MCP: `get_customer(5)`
5. Customer Data Agent → Router: Returns customer data
6. Router returns final response

### Scenario 2: Negotiation and Escalation
**Query**: "I want to cancel my subscription but I'm having billing issues. My customer ID is 1."

**A2A Flow**:
1. Router detects multiple intents: cancellation + billing issue
2. Router → Customer Data Agent: "Get customer 1 info"
3. Customer Data Agent returns customer details + ticket history
4. Router → Support Agent: "Customer wants to cancel but has billing issues"
5. Support Agent → Router: "Create escalation ticket"
6. Router → Customer Data Agent: "Create high-priority ticket"
7. Agents coordinate final response

### Scenario 3: Multi-Step Coordination
**Query**: "Show me the names of all active customers who have closed tickets."

**A2A Flow**:
1. Router decomposes query into subtasks
2. Router → Customer Data Agent: "List all active customers"
3. Customer Data Agent returns list of 12 active customers
4. Router → Customer Data Agent: "Get ticket history for IDs: 1,2,3..."
5. Customer Data Agent returns all tickets
6. Router filters customers with closed tickets
7. Router synthesizes final list of customer names

---

## Implementation Details

### Core Components

**MCP Server** ([`src/mcp_server.py`](src/mcp_server.py)):
- Flask server with 5 database tools
- JSON-RPC 2.0 protocol implementation
- Error handling and logging
- Database connection management

**Agent Definitions** ([`src/agents.py`](src/agents.py)):
- Customer Data Agent with MCP integration
- Support Agent with escalation logic
- Agent cards and instructions
- Tool integration configuration

**Configuration** ([`src/config.py`](src/config.py)):
- Centralized environment variables
- API key management
- Server URL configuration

**Router** ([`src/router.py`](src/router.py)):
- A2A coordination logic
- Agent communication client
- Workflow orchestration

---

## Setup & Installation

### Prerequisites
- Python 3.11+
- Google API key (for Gemini LLM)
- Ngrok token (for public URL exposure)

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

**Using Google Colab:**

1. Add to Colab Secrets:
   - `a5-key`: Your Google API key
   - `MCP_SERVER_URL`: Your MCP server URL (via Ngrok)

2. Open [`agent_to_agent_demo.ipynb`](agent_to_agent_demo.ipynb) in Google Colab

3. Run all cells sequentially
   - Notebook automatically starts agent servers on ports 10020 and 10021

### Sample Output

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

## Technologies Used

- **Google Agent Development Kit (ADK)**: Agent framework and A2A SDK
- **Google Gemini**: LLM for routing and decision-making
- **Flask**: MCP server implementation
- **SQLite**: Customer database
- **Ngrok**: Public URL tunneling
- **Python 3.11**: Core implementation language

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

Built as part of The University of Chicago's Applied Generative AI Agents and Multimodal Intelligence course (November 2025).

---

## Repository

GitHub: https://github.com/bhstoller/multi-agent-customer-service
