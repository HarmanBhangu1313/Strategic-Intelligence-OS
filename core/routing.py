"""
Auto-extracted from ARIA_Strategic_Intelligence_OS.ipynb
"""

    """LangGraph multi-agent orchestration: StateGraph nodes communicate through typed state objects.
    Use conditional edges for intent routing. ToolNode handles tool execution. MemorySaver provides
    cross-turn memory. Checkpointing enables fault tolerance in production deployments.""",


llm      = ChatGroq(model="llama-3.3-70b-versatile",api_key=groq_api_key_1)
llm_fast = ChatGroq(model="llama-3.1-8b-instant",api_key=groq_api_key_1)   # routing / critic
print("✅ LLMs initialized: 70B (main) | 8B (router/critic)")


ROUTER_PROMPT_V2 = """You are an enterprise analytics intent classifier.
Classify the user query into EXACTLY ONE of these routes:


print("✅ Intent router V2 ready (7 routes).")

# ── Entry ──────────────────────────────────────────────────────────────────────
graph.add_edge(START, "router_node")

Respond ONLY with valid JSON (no markdown):
{
  "query_intent": "one sentence summary",
  "complexity": "low|medium|high",
  "subtasks": [
    {"id": "t1", "type": "market_analysis", "question": "...", "priority": 1},
    {"id": "t2", "type": "competitor_research", "question": "...", "priority": 2}
  ],
  "estimated_agents": 3,
  "key_uncertainties": ["...", "..."]
}
"""