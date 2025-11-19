# Multi-Agent Customer Service System

A production-ready agent-to-agent (A2A) communication system using Google's Agent Development Kit (ADK) and A2A SDK. This system demonstrates how multiple specialized AI agents can coordinate to handle complex customer service queries through intelligent routing and orchestration.

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│         Router Orchestrator (LLM-powered)               │
│  - Analyzes user queries                                │
│  - Routes to appropriate agents                         │
│  - Coordinates multi-agent workflows                    │
└──────────────────┬──────────────────┬──────────────────┘
                   │                  │
        ┌──────────▼────────┐  ┌─────▼──────────────┐
        │ Customer Data     │  │ Support Agent      │
        │ Agent (10020)     │  │ (10021)            │
        │                  │  │                    │
        │ - get_customer   │  │ - Advice           │
        │ - list_customers │  │ - Troubleshooting  │
        │ - update_customer│  │ - Escalation       │
        │ - create_ticket  │  │                    │
        │ - get_history    │  │                    │
        └────────┬─────────┘  └─────┬──────────────┘
                 │                  │
        ┌────────▼──────────────────▼────────┐
        │    MCP Server (Flask)               │
        │    - Database operations            │
        │    - MCP tool exposure              │
        │    - SQLite (support.db)            │
        └─────────────────────────────────────┘
```

## Components

### 1. **config.py**
Centralized configuration management:
- Google API key and LLM model settings
- Server URLs and ports (for A2A communication)
- Database path configuration
- Ngrok settings for public tunneling
- Environment variable handling

### 2. **agents.py**
Agent definitions using Google ADK:
- **Customer Data Agent**: Handles customer information, tickets, and database operations
- **Support Agent**: Provides support advice and escalation guidance
- Includes agent instructions/system prompts
- MCP tool definitions for each agent

### 3. **mcp_server.py**
Flask-based MCP server:
- Exposes database operations as MCP tools
- Handles JSON-RPC requests from agents
- Supports ngrok for public URL exposure
- Tools: `get_customer`, `list_customers`, `update_customer`, `create_ticket`, `get_customer_history`

### 4. **router.py**
Orchestration logic:
- **A2ASimpleClient**: Manages agent-to-agent HTTP communication
- **RouterOrchestrator**: LLM-powered router that:
  - Analyzes user queries
  - Decides which agents to call
  - Coordinates multi-step workflows
  - Synthesizes final responses

### 5. **database_setup.py**
Initializes SQLite database with:
- Customer table (name, email, phone, status)
- Tickets table (customer_id, issue, status, priority)
- Test data for demonstration

## Setup & Installation

### Prerequisites
- Python 3.11+
- Google API key (get one at https://aistudio.google.com/app/apikey)
- Optional: Ngrok account for public URL exposure

### Local Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/bhstoller/multi-agent-customer-service.git
   cd multi-agent-customer-service
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` file:**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your configuration:
   ```
   GOOGLE_API_KEY=your_api_key_here
   MCP_SERVER_URL=http://localhost:10020/mcp
   NGROK_AUTHTOKEN=your_ngrok_token_here  # Optional
   ```

5. **Initialize database:**
   ```bash
   python database_setup.py
   ```

## Running the System

### Option 1: Local Development (Two Terminals)

**Terminal 1 - Start MCP Server:**
```bash
python src/mcp_server.py
```
Output:
```
Starting MCP Server...
✓ Agent servers initialized
Starting Flask server on 0.0.0.0:10020...
```

**Terminal 2 - Run Demo Notebook:**
```bash
jupyter notebook agent_to_agent_demo.ipynb
```

### Option 2: Google Colab (Recommended for Demo)

1. Open `agent_to_agent_demo.ipynb` in Google Colab
2. Add to Colab Secrets:
   - `a5-key`: Your Google API key
   - `MCP_SERVER_URL`: Your MCP server URL (ngrok or localhost)
3. Run cells sequentially
4. The notebook will automatically start agent servers

## Usage Examples

### Simple Query (Single Agent)
```python
query = "Get customer information for customer ID 5"

# Router analyzes query → calls Customer Data Agent → returns customer details
result = await router.process_query(query)
```

### Multi-Agent Coordination
```python
query = "I want to cancel my subscription but I'm having billing issues. My customer ID is 1."

# Router coordinates:
# 1. Calls Customer Data Agent to get customer info and ticket history
# 2. Calls Support Agent for escalation guidance
# 3. Creates high-priority support ticket
# 4. Returns coordinated response to customer
result = await router.process_query(query)
```

### Complex Multi-Step Query
```python
query = "Show me the names of all active customers who have closed tickets."

# Router decomposes query:
# 1. Gets list of active customers
# 2. Retrieves ticket history for all customers
# 3. Filters for closed tickets
# 4. Returns aggregated report
result = await router.process_query(query)
```

## API Reference

### MCP Tools

**get_customer(customer_id: int)**
- Returns customer record by ID
- Example: `{"customer": {"id": 5, "name": "Charlie Brown", ...}}`

**list_customers(status: str = None)**
- Lists customers, optionally filtered by status ("active" or "disabled")
- Returns: `{"customers": [...], "count": 5}`

**update_customer(customer_id: int, name: str = None, email: str = None, phone: str = None)**
- Updates customer information
- Returns updated customer record

**create_ticket(customer_id: int, issue: str, priority: str)**
- Creates support ticket for customer
- Priority: "low", "medium", "high"
- Returns: `{"ticket": {...}, "success": true}`

**get_customer_history(customer_id: int)**
- Returns all tickets for a customer
- Returns: `{"history": [...], "count": 5}`

### Router Methods

**async router.process_query(user_query: str) → str**
- Processes user query through router orchestrator
- Returns final response string
- Max 15 reasoning steps per query

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | Required | Google Generative AI API key |
| `MCP_SERVER_URL` | Required | Base URL for MCP server |
| `LLM_MODEL` | `gemini-2.0-flash` | Model to use for LLM |
| `NGROK_AUTHTOKEN` | Optional | Ngrok auth token for public URL |
| `DB_PATH` | `support.db` | Path to SQLite database |
| `LOG_LEVEL` | `INFO` | Logging level |
| `DEBUG` | `false` | Enable debug mode |

### Server Ports

- **Customer Data Agent**: `10020`
- **Support Agent**: `10021`
- **Router Agent**: `10040` (not used in current setup)

## File Structure

```
multi-agent-customer-service/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── .gitignore                   # Git ignore rules
├── LICENSE                      # MIT License
├── database_setup.py            # Database initialization
├── agent_to_agent_demo.ipynb    # Demo notebook
├── src/
│   ├── __init__.py
│   ├── config.py                # Configuration management
│   ├── agents.py                # Agent definitions
│   ├── mcp_server.py            # MCP server implementation
│   └── router.py                # Router orchestration
└── notebooks/                   # Reference notebooks (optional)
```

## Development

### Adding a New Agent

1. Define agent in `src/agents.py`:
```python
new_agent = Agent(
    name="new_agent",
    instructions="Your agent instructions...",
)
new_agent_card = AgentCard(agent=new_agent)
```

2. Add to router configuration in `src/router.py`
3. Define tools and capabilities in agent instructions

### Adding a New MCP Tool

1. Implement function in `src/mcp_server.py`:
```python
def my_tool(param: str) -> Dict[str, Any]:
    """Tool description"""
    return {"result": "..."}
```

2. Add to `MCP_TOOLS` list with schema
3. Add to `tool_functions` in `handle_tools_call()`

## Performance Notes

- **Ngrok**: Uses free tier (limited bandwidth, random URLs restart)
- **Query Complexity**: Max 15 reasoning steps per query
- **Database**: SQLite suitable for demos; use PostgreSQL for production
- **Concurrency**: Single-threaded; use async for multiple queries

## Troubleshooting

### "MCP_SERVER_URL not set"
- Check `.env` file exists in repo root
- Verify `MCP_SERVER_URL` is set and accessible
- For Colab: Add `MCP_SERVER_URL` to Colab Secrets

### "Port 10020 already in use"
```bash
# Kill existing process
lsof -i :10020
kill -9 <PID>
```

### "Agent server connection failed"
- Ensure MCP server is running: `python src/mcp_server.py`
- Check ngrok tunnel is active: `ngrok http 10020`
- Verify firewall allows connections

### "Database file not found"
- Run initialization: `python database_setup.py`
- Check `DB_PATH` in `.env`

## Dependencies

Key packages:
- `google-adk>=1.9.0` - Google Agent Development Kit
- `a2a-sdk>=0.3.0` - Agent-to-Agent SDK
- `google-generativeai>=0.5.0` - Google Gemini API
- `flask>=2.3.0` - MCP server framework
- `uvicorn>=0.24.0` - ASGI server
- `httpx>=0.25.0` - Async HTTP client
- `pyngrok>=5.2.0` - Ngrok Python bindings

See `requirements.txt` for full list.

## License

MIT License - see LICENSE file for details

## Author

Bradley Stoller

## Contributing

Pull requests welcome! Please ensure:
- Code follows existing style
- All imports are used
- Documentation is updated
- Tests pass

## Resources

- [Google ADK Documentation](https://ai.google.dev/docs/adk)
- [A2A SDK Documentation](https://github.com/google/ai-agent-sdk)
- [Google Generative AI](https://ai.google.dev)
- [Ngrok Documentation](https://ngrok.com/docs)

## Support

For issues or questions:
1. Check troubleshooting section above
2. Open an issue on GitHub
3. Review notebook examples in `agent_to_agent_demo.ipynb`

---

**Last Updated**: November 2025