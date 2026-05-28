"""
Auto-extracted from ARIA_Strategic_Intelligence_OS.ipynb
"""

# Install ALL external dependencies required for the entire script
!pip install -q \
    langgraph \
    langchain-groq \
    langchain-core \
    langchain-community \
    langchain-huggingface \
    huggingface-hub \
    pypdf \
    faiss-cpu \
    rank-bm25 \
    gradio \
    plotly \
    python-dotenv

# ── Retrieval ──────────────────────────────────────────────────────────────────
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# ── Sparse Retrieval (BM25) ───────────────────────────────────────────────────
try:
    from rank_bm25 import BM25Okapi
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "rank-bm25", "-q"])
    from rank_bm25 import BM25Okapi

    """RAG (Retrieval-Augmented Generation) architecture best practices: Use hybrid retrieval combining
    dense vector search with BM25 sparse retrieval. Apply Reciprocal Rank Fusion to merge ranked lists.
    Chunk size of 512 tokens with 10% overlap works well for technical documents. Evaluate with RAGAS.""",

    """Observability in ML systems: Track token latency, retrieval latency, SQL execution time,
    and confidence scores per request. Store telemetry in structured logs. Build dashboards showing
    route distribution, p95/p99 latencies, and error rates.""",

# ── FAISS + BM25 index ────────────────────────────────────────────────────────
print("🔧 Building FAISS + BM25 index...")
embeddings_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)

doc_objects = [
    Document(
        page_content=d,
        metadata={
            "source": ("crunchbase_startups" if i >= len(ENTERPRISE_DOCS) and i < len(ENTERPRISE_DOCS)+len(startup_corpus)
                       else "crunchbase_investors" if i >= len(ENTERPRISE_DOCS)+len(startup_corpus)
                       else f"enterprise_kb_{i}"),
            "doc_id": i,
            "type": ("startup" if i >= len(ENTERPRISE_DOCS) and i < len(ENTERPRISE_DOCS)+len(startup_corpus)
                     else "investor" if i >= len(ENTERPRISE_DOCS)+len(startup_corpus)
                     else "enterprise")
        }
    )
    for i, d in enumerate(ENTERPRISE_DOCS_EXTENDED)
]
chunks = splitter.split_documents(doc_objects)
faiss_store = FAISS.from_documents(chunks, embeddings_model)
faiss_retriever = faiss_store.as_retriever(search_type="similarity", search_kwargs={"k": 6})

tokenized_corpus = [doc.page_content.lower().split() for doc in chunks]
bm25_index = BM25Okapi(tokenized_corpus)
print(f"✅ Extended hybrid index ready: {len(chunks)} chunks (FAISS + BM25)")


def hybrid_retrieve(query: str, top_k: int = 4) -> list:
    """Combine FAISS (dense) + BM25 (sparse) results via RRF."""
    dense_results = faiss_retriever.invoke(query)
    tokens = query.lower().split()
    bm25_scores = bm25_index.get_scores(tokens)
    top_indices = np.argsort(bm25_scores)[::-1][:8]
    sparse_results = [chunks[i] for i in top_indices if bm25_scores[i] > 0]
    fused = reciprocal_rank_fusion([dense_results, sparse_results])
    return fused[:top_k]

test_r = hybrid_retrieve("venture capital fund investment")
print("✅ Hybrid RRF retrieval verified.")
print(f"   Top result type: {test_r[0].metadata.get('type','?')} | snippet: {test_r[0].page_content[:80]}...")


@dataclass
class TelemetryRecord:
    request_id: str
    timestamp: str
    query: str
    route: str                    # analytics|rag|forecasting|anomaly|investor|ecosystem|general
    total_latency_ms: float
    retrieval_latency_ms: float
    sql_latency_ms: float
    llm_latency_ms: float
    estimated_tokens: int
    confidence_score: float       # 0.0–1.0
    sources_cited: int
    validator_passed: bool
    sql_retry_count: int = 0      # NEW — tracks correction loop frequency
    agent_type: str = "standard"  # NEW — "standard"|"investor"|"ecosystem"|"forecasting"|"anomaly"
    db_queried: str = "enterprise"# NEW — "enterprise"|"crunchbase"|"both"
    error: Optional[str] = None


class EnterpriseState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    route: Optional[str]           # analytics|rag|forecasting|anomaly|investor|ecosystem|general
    request_id: Optional[str]
    t_start: Optional[float]
    retrieval_ms: Optional[float]
    sql_ms: Optional[float]
    validator_passed: Optional[bool]
    confidence_score: Optional[float]
    sources: Optional[list]
    sql_query: Optional[str]
    sql_result: Optional[str]
    sql_retry_count: Optional[int]  # NEW — retry loop counter

def router_node(state: EnterpriseState) -> EnterpriseState:
    """Classify query into one of 7 routes."""
    t0 = time.time()
    query = state["messages"][-1].content
    resp = llm_fast.invoke([
        SystemMessage(content=ROUTER_PROMPT_V2),
        HumanMessage(content=query)
    ])
    route = resp.content.strip().lower()
    if route not in VALID_ROUTES:
        route = "general"
    print(f"🔀 Route: [{route.upper()}] | query: '{query[:60]}...'")
    return {
        **state,
        "route": route,
        "request_id": str(uuid.uuid4())[:8],
        "t_start": t0,
        "retrieval_ms": 0.0,
        "sql_ms": 0.0,
        "validator_passed": None,
        "confidence_score": None,
        "sources": [],
        "sql_query": None,
        "sql_result": None,
        "sql_retry_count": 0,
    }


def rag_node(state: EnterpriseState) -> EnterpriseState:
    """Hybrid retrieval (FAISS + BM25 + RRF) → grounded answer with citations."""
    query = state["messages"][-1].content
    t_ret = time.time()
    docs = hybrid_retrieve(query, top_k=4)
    retrieval_ms = (time.time() - t_ret) * 1000
    context = "\n\n".join([f"[Doc {i+1}]: {d.page_content}" for i, d in enumerate(docs)])
    sources = list(set(d.metadata.get("source", "kb") for d in docs))
    rag_prompt = f"""You are an enterprise knowledge analyst. Use ONLY the provided context to answer.

Context (hybrid FAISS + BM25 + RRF retrieval):
{context}

Instructions:
- Ground every claim in the context above.
- If the context does not answer the question, say so clearly.
- Structure: Key Finding → Supporting Details → Implications.
- End with: Sources: {', '.join(sources)}
"""
    response = llm.invoke([HumanMessage(content=rag_prompt)])
    return {
        **state,
        "messages": [*state["messages"],
                     response.__class__(content=f"🔍 **Knowledge Retrieval**\n\n{response.content}")],
        "retrieval_ms": retrieval_ms,
        "confidence_score": 0.88,
        "sources": sources,
    }

    # RAG: investor narratives
    t_ret = time.time()
    docs = hybrid_retrieve(f"investor venture capital {query}", top_k=3)
    retrieval_ms = (time.time() - t_ret) * 1000
    rag_context = "\n".join(d.page_content for d in docs)

Answer with:
1. Investor tier analysis (top-tier vs emerging)
2. Notable fund sizes and recent activity
3. Geographic investment concentration
4. Investment focus areas by sector
5. One actionable insight for an entrepreneur or LP
Ground every claim in the data above.
"""
    response = llm.invoke([HumanMessage(content=combined_prompt)])
    final = (f"💼 **Investor Intelligence**\n\n{response.content}\n\n---\n"
             f"*SQL: {sql_ms:.1f}ms | RAG: 3 docs ({retrieval_ms:.0f}ms)*")
    return {
        **state,
        "messages": [*state["messages"], response.__class__(content=final)],
        "sql_ms": sql_ms,
        "retrieval_ms": retrieval_ms,
        "confidence_score": 0.83,
        "sources": ["cb_funds","cb_objects","crunchbase_rag"],
    }


def telemetry_node(state: EnterpriseState) -> EnterpriseState:
    """Log complete telemetry record with retry count, agent type, and DB queried."""
    t_end = time.time()
    t_start = state.get("t_start") or t_end
    total_ms = (t_end - t_start) * 1000
    query = ""
    for msg in reversed(state["messages"]):
        if hasattr(msg, "type") and msg.type == "human":
            query = msg.content
            break
    last_response = state["messages"][-1].content if state["messages"] else ""
    est_tokens = max(1, len(last_response.split()) * 4 // 3)
    route = state.get("route","general")
    db_queried = "crunchbase" if route in ["ecosystem","investor"] else (
        "both" if route in ["forecasting","anomaly"] else "enterprise"
    )
    record = TelemetryRecord(
        request_id=state.get("request_id","unknown"),
        timestamp=datetime.now().isoformat(),
        query=query[:80],
        route=route,
        total_latency_ms=round(total_ms, 1),
        retrieval_latency_ms=round(state.get("retrieval_ms",0) or 0, 1),
        sql_latency_ms=round(state.get("sql_ms",0) or 0, 1),
        llm_latency_ms=round(total_ms-(state.get("retrieval_ms",0) or 0)-(state.get("sql_ms",0) or 0), 1),
        estimated_tokens=est_tokens,
        confidence_score=round(state.get("confidence_score",0.8) or 0.8, 3),
        sources_cited=len(state.get("sources",[]) or []),
        validator_passed=state.get("validator_passed", True),
        sql_retry_count=state.get("sql_retry_count",0) or 0,
        agent_type=route,
        db_queried=db_queried,
        error=None,
    )
    log_telemetry(record)
    print(f"  📊 Telemetry | {total_ms:.0f}ms | route:{record.route} | "
          f"conf:{record.confidence_score:.2f} | retries:{record.sql_retry_count} | db:{db_queried}")
    return state

    gr.Markdown("""
    # 🏢 ARIA — Enterprise Intelligence & Agentic Analytics Platform
    **Powered by:** LangGraph · Hybrid RAG (FAISS + BM25 + RRF) · Text-to-SQL (Dual-DB) ·
    Crunchbase Ecosystem · Anomaly Detection · Forecasting · Critic/Validator · Telemetry
    """)

```
[START]
   │
[Intent Router] ──── LLaMA 8B (7-route classification)
   │
   ├── analytics    ──► [Text-to-SQL V2]        ──► enterprise_intelligence.db + crunchbase_ecosystem.db
   ├── rag          ──► [Hybrid RAG Agent]       ──► FAISS + BM25 + RRF (enterprise + startup corpus)
   ├── forecasting  ──► [Forecasting Agent]      ──► product_kpis + CB funding trends
   ├── anomaly      ──► [Anomaly Agent]          ──► ops Z-score + sector peer funding + acq clustering
   ├── investor     ──► [Investor Agent]         ──► cb_funds + cb_objects + RAG
   ├── ecosystem    ──► [Ecosystem Agent]        ──► cb_objects sector/geo rollup
   └── general      ──► [Conversation Agent]    ──► LLaMA 70B
        │
   [Critic/Validator Node] ──► Hallucination check + Confidence scoring
        │
   [Telemetry Node] ──► route | latency | retries | db_queried | confidence
        │
     [END]
```

| Component | Technology | Extension |
|---|---|---|
| Orchestration | LangGraph StateGraph | 9 nodes, 7 routes (was 8/5) |
| Dense Retrieval | FAISS + HuggingFace | Extended with 3k+ startup narratives |
| Sparse Retrieval | BM25Okapi | Extended corpus |
| Fusion | Reciprocal Rank Fusion | k=60 |
| Structured Query | Text-to-SQL V2 | Dual-DB + retry loop (max 2) |
| Crunchbase DB | SQLite 9-table relational | 18 indexes, WAL journal |
| Anomaly Detection | Z-score peer-group | Ops + Funding + Acquisition |
| Investor Agent | SQL + RAG hybrid | cb_funds + investor corpus |
| Ecosystem Agent | Sector/Geo rollup SQL | cb_objects multi-dim |
| Forecasting | Linear regression | KPI + CB funding trends |
| Validation | Critic LLM Node | Fail-open, confidence penalty |
| Telemetry | Extended TelemetryRecord | retries + agent_type + db_queried |
| LLM Backbone | Groq (LLaMA 70B + 8B) | Low-latency inference |
| Dashboard | Gradio + Plotly | 6 tabs (was 4) |
            """)


class StrategicState(TypedDict):
    # ── Inherited from EnterpriseState ──────────────────────────────────────
    messages: Annotated[list[BaseMessage], add_messages]
    route: Optional[str]
    request_id: Optional[str]
    t_start: Optional[float]
    retrieval_ms: Optional[float]
    sql_ms: Optional[float]
    validator_passed: Optional[bool]
    confidence_score: Optional[float]
    sources: Optional[list]
    sql_query: Optional[str]
    sql_result: Optional[str]
    sql_retry_count: Optional[int]

    # ── Strategic OS extensions ───────────────────────────────────────────────
    strategic_query: Optional[str]           # Original high-level user query
    subtasks: Optional[list]                 # Planner decomposition output
    market_analysis: Optional[dict]          # Market Analyst agent output
    competitor_analysis: Optional[dict]      # Competitor intelligence
    swot: Optional[dict]                     # SWOT analysis
    risk_assessment: Optional[dict]          # Risk matrix
    opportunities: Optional[list]            # Detected opportunities
    strategic_plan: Optional[dict]           # Final recommendations
    evidence_quality: Optional[float]        # 0.0–1.0 evidence score
    critique_log: Optional[list]             # Self-correction trace
    retrieval_queries: Optional[list]        # Query rewrite history
    retry_reason: Optional[str]             # Why retry was triggered
    final_report: Optional[str]             # Executive intelligence report
    report_confidence: Optional[float]      # Final confidence score
    execution_trace: Optional[list]         # Live agent execution trace

    print(f"📋 Planner | {len(plan.get('subtasks',[]))} subtasks | complexity: {plan.get('complexity')}")
    return {
        **state,
        "strategic_query": query,
        "subtasks": plan.get("subtasks", []),
        "execution_trace": trace,
        "request_id": str(uuid.uuid4())[:8],
        "t_start": t0,
        "retrieval_ms": 0.0,
        "sql_ms": 0.0,
        "critique_log": [],
        "retrieval_queries": [query],
        "evidence_quality": 0.0,
        "sql_retry_count": 0,
    }

    # Hybrid retrieval for market evidence
    t_ret = time.time()
    market_docs = hybrid_retrieve(f"market size trends analysis {query}", top_k=4)
    retrieval_ms = (time.time() - t_ret) * 1000
    context = "\n\n".join(d.page_content[:300] for d in market_docs)

    print(f"📊 MarketAnalyst | conf: {confidence:.2f} | {len(market_docs)} docs | {retrieval_ms:.0f}ms")
    return {
        **state,
        "market_analysis": analysis,
        "swot": analysis.get("swot"),
        "evidence_quality": evidence_quality,
        "retrieval_ms": retrieval_ms,
        "sql_ms": sql_ms,
        "execution_trace": trace,
        "critique_log": critique_log,
    }


QUERY_REWRITER_SYSTEM = """You are a retrieval query optimizer.
Given an original query and evidence quality score, rewrite it to retrieve better evidence.

def strategic_retrieval_node(state: StrategicState) -> StrategicState:
    """Retrieve evidence for all subtasks. Rewrite queries if evidence quality is low."""
    query = state.get("strategic_query") or state["messages"][-1].content
    subtasks = state.get("subtasks") or []
    evidence_quality = state.get("evidence_quality") or 0.0
    retrieval_queries = state.get("retrieval_queries") or [query]
    trace = state.get("execution_trace") or []
    critique_log = state.get("critique_log") or []

    # ── Query rewrite if evidence is weak ────────────────────────────────────
    active_query = query
    if evidence_quality < 0.65 and len(retrieval_queries) < 4:
        trace.append({
            "agent": "RetrievalAgent",
            "status": "rewriting",
            "timestamp": datetime.now().isoformat(),
            "action": f"Evidence quality {evidence_quality:.2f} < 0.65 — triggering query rewrite",
        })
        rewrite_resp = llm_fast.invoke([
            SystemMessage(content=QUERY_REWRITER_SYSTEM),
            HumanMessage(content=f"Original query: {query}\nEvidence quality: {evidence_quality:.2f}\nRewrite to improve retrieval.")
        ])
        active_query = rewrite_resp.content.strip()
        retrieval_queries.append(active_query)
        critique_log.append({
            "step": "query_rewrite",
            "original": query,
            "rewritten": active_query,
            "reason": f"Evidence quality below threshold ({evidence_quality:.2f})"
        })
        print(f"  🔄 Query rewritten: '{active_query[:60]}'")

    trace.append({
        "agent": "RetrievalAgent",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "action": f"Retrieving for {len(subtasks)} subtasks..."
    })

    retrieval_ms = (time.time() - t_ret) * 1000
    total_docs = sum(len(v) for v in all_docs.values())
    new_quality = min(1.0, 0.4 + 0.08 * total_docs)

    trace.append({
        "agent": "RetrievalAgent",
        "status": "complete",
        "timestamp": datetime.now().isoformat(),
        "action": f"Retrieved {total_docs} docs across {len(all_docs)} subtasks | {retrieval_ms:.0f}ms",
        "output_preview": f"Evidence quality improved: {evidence_quality:.2f} → {new_quality:.2f}"
    })

    print(f"🔍 RetrievalAgent | {total_docs} docs | quality: {new_quality:.2f} | {retrieval_ms:.0f}ms")
    return {
        **state,
        "sources": all_docs,
        "evidence_quality": new_quality,
        "retrieval_ms": retrieval_ms,
        "retrieval_queries": retrieval_queries,
        "execution_trace": trace,
        "critique_log": critique_log,
    }

print("✅ Strategic Retrieval agent ready (with query rewriting).")

def strategic_critic_node(state: StrategicState) -> StrategicState:
    """Validate strategic analysis. Trigger retry if evidence is insufficient."""
    market_analysis = state.get("market_analysis") or {}
    evidence_quality = state.get("evidence_quality") or 0.0
    retrieval_queries = state.get("retrieval_queries") or []
    critique_log = state.get("critique_log") or []
    trace = state.get("execution_trace") or []

    critique_input = f"""Evidence Quality Score: {evidence_quality:.2f}
Market Analysis Confidence: {market_analysis.get('confidence_score', 0.0)}
Market Overview: {market_analysis.get('market_overview','N/A')[:300]}
TAM: ${market_analysis.get('tam_usd_bn','N/A')}B
Evidence Sources: {market_analysis.get('evidence_sources',[])}
Retrieval Query Count: {len(retrieval_queries)}
SWOT populated: {bool(market_analysis.get('swot',{}).get('strengths'))}
"""

    passed = verdict.get("passed", True)
    final_confidence = float(verdict.get("overall_confidence", evidence_quality))
    retry_needed = verdict.get("retry_recommended", False) and len(retrieval_queries) < 4


def should_retry_or_proceed(state: StrategicState) -> str:
    """Conditional edge: retry retrieval or proceed to report generation."""
    if state.get("retry_reason") and len(state.get("retrieval_queries", [])) < 4:
        return "strategic_retrieval_node"
    return "report_generator_node"

---
**Platform Telemetry**
- Evidence Quality: {evidence_quality:.0%}
- Final Confidence: {report_confidence:.0%}
- Self-Corrections: {len([c for c in critique_log if c.get('retry_recommended')])}
- Retrieval Queries Used: {len(state.get('retrieval_queries',[]))}
- Agent Execution Steps: {len(trace)}
"""

# Register nodes
strategic_graph.add_node("planner_node",             planner_node)
strategic_graph.add_node("strategic_retrieval_node", strategic_retrieval_node)
strategic_graph.add_node("market_analyst_node",      market_analyst_node)
strategic_graph.add_node("strategic_critic_node",    strategic_critic_node)
strategic_graph.add_node("report_generator_node",    report_generator_node)
strategic_graph.add_node("telemetry_node",           telemetry_node)

# Wire the pipeline
strategic_graph.add_edge(START,                       "planner_node")
strategic_graph.add_edge("planner_node",              "strategic_retrieval_node")
strategic_graph.add_edge("strategic_retrieval_node",  "market_analyst_node")
strategic_graph.add_edge("market_analyst_node",       "strategic_critic_node")

# Self-correction loop: Critic can route back to Retrieval or forward to Report
strategic_graph.add_conditional_edges(
    "strategic_critic_node",
    should_retry_or_proceed,
    {
        "strategic_retrieval_node": "strategic_retrieval_node",
        "report_generator_node":    "report_generator_node",
    }
)

print("✅ Strategic Intelligence Graph compiled.")
print("   Nodes: Planner → Retrieval → MarketAnalyst → Critic ↩️ [retry] → ReportGenerator → Telemetry")
print("   Self-correction: max 3 retrieval retries before forced report generation")

    return {
        "report": final_report,
        "trace": result.get("execution_trace", []),
        "confidence": result.get("report_confidence", result.get("confidence_score", 0.0)),
        "critique_log": result.get("critique_log", []),
        "evidence_quality": result.get("evidence_quality", 0.0),
        "retrieval_queries": result.get("retrieval_queries", []),
        "subtasks": result.get("subtasks", []),
        "market_analysis": result.get("market_analysis", {}),
        "swot": result.get("swot", {}),
    }


# Demo query
print("\n" + "="*70)
print("🧠 STRATEGIC INTELLIGENCE OS — DEMO")
print("="*70)
demo_query = "Analyze launching an AI tutoring startup in India"
print(f"\n🎯 Query: '{demo_query}'")
print("-"*70)
result = run_strategic_analysis(demo_query, thread_id="demo_001")
print("\n" + result["report"][:800] + "...")
print("\n📊 EXECUTION TELEMETRY:")
for step in result["trace"]:
    agent = step.get("agent","?")
    status = step.get("status","?")
    action = step.get("action","")[:80]
    print(f"  [{agent:<20}] [{status:<15}] {action}")
print(f"\n✅ Final Confidence: {result['confidence']:.0%}")
print(f"   Evidence Quality: {result['evidence_quality']:.0%}")
print(f"   Self-corrections: {len([c for c in result['critique_log'] if c.get('retry_recommended')])}")
print(f"   Retrieval queries: {len(result['retrieval_queries'])}")

> Powered by **ARIA Extended Architecture** — LangGraph · FAISS+BM25+RRF · Dual-DB SQL · Critic Loop · Live Observability

        status = f"✅ Complete | Confidence: {conf:.0%} | Evidence: {ev_q:.0%}"
        report = result.get("report","")
        report_stats = f"{len(report)} chars | {len(result.get('subtasks',[]))} subtasks | {len(result.get('retrieval_queries',[]))} queries"