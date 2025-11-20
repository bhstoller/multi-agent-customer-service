# Lessons Learned & Challenges

## What I Learned

1. **Agent Coordination Requires Explicit Communication Protocols**: From this assignment, one of the main things I learned was that managing state and information flow between multiple agents is significantly more complex than a single agent. Without explicit logging at every coordination point and clear communication protocols between agents, debugging multi-agent systems was very difficult to do. While the A2A pattern provides good default instructions, the orchestrator had to be really strong in order to manage the conversation effectively.

2. **MCP as a Critical Interface Layer**: I learned fairly early on into the assignment that the entire system relied on the MCP server, which had to be working for everyhting else to work as well. Specifically, proper tool definition, and timeout configurations were missing in my early attempts, which caused silent failures to cascade through my system. Thus, I learned that MCP tools need to be very well-defined with very clear error messages for debugging.

3. **LLM-Powered Routing Demands Careful Prompt Engineering**: I also learned how helpful LLM tools are for helping decide which agents to call. Specifically, I found that LLMs responded well to structure (ie my prompt/instructions) and were therefore able to list available agents, provide clear decision criteria, and specify the output format. Before using the LLM (and a set of instructions), my first router would sometimes make different decisions for the same query.

## Challenges Overcome

1. **Understanding the Router's Architecture**: The biggest challenge that I had to overcome was initially implementing the router as a `SequentialAgent`. However, I ultimately realized that this configuration wasn't the right approach, especially since it could not be given any instructions (prompting). However, I was able to solve this by switching to a `RouterOrchestrator` (a custom python class) with Gemini LLM for reasoning and `A2ASimpleClient` for agent communicationm, which ended up being clearer and more flexible than having the router be a specialist agent.

2. **A2A Communication and Message Passing**: When starting the assignment, the A2A SDK's HTTP communication pattern wasn't very intuitive, and in my early attempts, I kept seeing my system fail silently or crash due to timeout misconfigurations. I ultimately solved this by building a more robust `A2ASimpleClient` with proper timeout configurations and agent card caching. Together, with explicit logging instructions, I was able to make debugging much easier.

3. **State Management Across Agents**: Lastly, tracking information flow between my specialist agents and ensuring that each of them had the necessary context for decisions was another big challenge early on. Specifically, my agents initially would lose track of information like customer IDs or forget to pass results between agents. However, I solved this by maintaining message history via the router (I required that all messages sent to Gemini included responses) and (again) adding logging at every coordination point.