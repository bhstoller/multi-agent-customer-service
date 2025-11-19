# Lessons Learned & Challenges

## What I Learned
1. **Agent Coordination Complexity**: Managing state and information flow between agents requires careful planning. The A2A pattern provides good abstractions but demands explicit communication protocols.

2. **MCP as a Bridge**: The MCP server acts as a critical interface between agents and external tools. Proper tool definition, error handling, and timeout management are essential for reliability.

3. **LLM-Powered Routing**: Using an LLM to decide routing provides flexibility but requires careful prompt engineering to ensure agents are called appropriately and consistently.

4. **Debugging Multi-Agent Systems**: With multiple agents running asynchronously, debugging requires comprehensive logging at every coordination point. Without it, issues are nearly impossible to trace.

## Challenges Overcome
1. **A2A Communication**: Initial challenge was understanding the A2A SDK's HTTP communication pattern. Solved by implementing a robust `A2ASimpleClient` with proper timeout and error handling.

2. **State Management**: Tracking information flow between agents (who knows what) was complex. Solved by maintaining message history and explicit logging of all agent calls.

3. **MCP Tool Reliability**: Tools occasionally timed out or failed silently. Solved by implementing comprehensive error handling, validation, and response formatting in each tool.

4. **ngrok URL Stability**: Ngrok tunnels would close between runs. Solved by implementing `ngrok.kill()` before creating new tunnels, ensuring clean connections.

5. **Agent Consistency**: Agents sometimes made different decisions with similar queries. Solved by refining system instructions with concrete examples and constraints.