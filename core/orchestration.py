"""
Auto-extracted from ARIA_Strategic_Intelligence_OS.ipynb
"""

# ── Core LLM / LangGraph ──────────────────────────────────────────────────────
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.documents import Document
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict, Annotated
from typing import Optional, Literal

print("✅ Hybrid RAG agent ready.")

print("✅ Investor intelligence agent ready.")

print("✅ Ecosystem intelligence agent ready.")

print("✅ Planner agent ready.")

print("✅ Market Analyst agent ready.")


from langgraph.graph import StateGraph, START, END

SOS_BANNER = """
# 🧠 Strategic Intelligence OS
### Autonomous · Multi-Agent · Self-Correcting · Enterprise-Grade
