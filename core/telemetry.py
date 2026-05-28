"""
Auto-extracted from ARIA_Strategic_Intelligence_OS.ipynb
"""

    # ── Table 3: Product KPIs ─────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS product_kpis (
        id INTEGER PRIMARY KEY, date TEXT, product TEXT,
        dau INTEGER, mau INTEGER, revenue REAL, churn_rate REAL,
        nps_score REAL, latency_p99_ms REAL, error_rate REAL
    )
    """)
    products_list = ["Platform Pro","Analytics Suite","DataBridge"]
    kpi_rows = []
    for prod in products_list:
        base_dau = {"Platform Pro":12000,"Analytics Suite":8500,"DataBridge":5200}[prod]
        base_rev = {"Platform Pro":85000,"Analytics Suite":62000,"DataBridge":41000}[prod]
        for week in range(24):
            date = (datetime(2024,1,1)+timedelta(weeks=week)).strftime("%Y-%m-%d")
            trend = 1 + 0.02*week
            noise = np.random.uniform(0.92, 1.08)
            kpi_rows.append((
                date, prod,
                int(base_dau*trend*noise), int(base_dau*trend*noise*4.2),
                round(base_rev*trend*noise, 2),
                round(np.random.uniform(1.2, 4.8), 2),
                round(np.random.uniform(38, 72), 1),
                round(np.random.uniform(120, 450), 1),
                round(np.random.uniform(0.1, 1.8), 3)
            ))
    cur.executemany("""
        INSERT OR IGNORE INTO product_kpis
        (date,product,dau,mau,revenue,churn_rate,nps_score,latency_p99_ms,error_rate)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, kpi_rows)

    # ── Table 4: Operational Metrics ──────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS operational_metrics (
        id INTEGER PRIMARY KEY, timestamp TEXT, service TEXT,
        cpu_pct REAL, memory_pct REAL, request_count INTEGER,
        error_count INTEGER, avg_latency_ms REAL, region TEXT
    )
    """)
    services = ["API Gateway","ML Inference","Data Pipeline","Auth Service","Query Engine"]
    op_rows = []
    for i in range(120):
        ts = (datetime(2024,6,1)+timedelta(hours=i)).strftime("%Y-%m-%d %H:%M:%S")
        svc = np.random.choice(services)
        anomaly = np.random.random() < 0.08
        op_rows.append((
            ts, svc,
            round(np.random.uniform(60,95) if anomaly else np.random.uniform(20,65), 1),
            round(np.random.uniform(70,92) if anomaly else np.random.uniform(30,70), 1),
            int(np.random.randint(800, 5000)),
            int(np.random.randint(50,300) if anomaly else np.random.randint(0,20)),
            round(np.random.uniform(400,1200) if anomaly else np.random.uniform(50,250), 1),
            np.random.choice(regions)
        ))
    cur.executemany("""
        INSERT OR IGNORE INTO operational_metrics
        (timestamp,service,cpu_pct,memory_pct,request_count,error_count,avg_latency_ms,region)
        VALUES (?,?,?,?,?,?,?,?)
    """, op_rows)

    """Product KPI frameworks: DAU/MAU ratio above 20% signals strong engagement. Churn rate below
    2% monthly is healthy for enterprise SaaS. NPS above 50 is excellent. P99 latency should stay
    under 500ms for interactive products. Error rate above 1% triggers SLA review.""",

telemetry_log: list = []

def log_telemetry(record: TelemetryRecord):
    telemetry_log.append(record)

def get_telemetry_df() -> pd.DataFrame:
    if not telemetry_log:
        return pd.DataFrame()
    return pd.DataFrame([asdict(r) for r in telemetry_log])

print("✅ Extended telemetry layer initialized.")


def execute_sql_safely_v2(sql: str) -> tuple:
    """Execute SQL against the appropriate DB; auto-detect from table names."""
    t0 = time.time()
    try:
        sql_clean = re.sub(r"```sql|```", "", sql).strip()
        uses_cb = any(t in sql_clean for t in CB_TABLES)
        db_path = CB_DB_PATH if uses_cb else DB_PATH
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(sql_clean, conn)
        conn.close()
        latency = (time.time() - t0) * 1000
        if df.empty:
            return "Query returned no results.", latency
        return df.head(50).to_string(index=False), latency
    except Exception as e:
        return f"SQL ERROR: {e}", (time.time() - t0) * 1000

    ops_anomalies = []
    for svc in df_ops["service"].unique():
        svc_df = df_ops[df_ops["service"] == svc].copy()
        for col in ["cpu_pct","error_count","avg_latency_ms"]:
            vals = svc_df[col].values
            mean, std = vals.mean(), vals.std()
            if std < 1e-6:
                continue
            z_scores = np.abs((vals - mean) / std)
            anomaly_mask = z_scores > 2.5
            if anomaly_mask.sum() > 0:
                worst_idx = np.argmax(z_scores)
                ops_anomalies.append({
                    "service": svc, "metric": col,
                    "anomaly_count": int(anomaly_mask.sum()),
                    "worst_value": round(float(vals[worst_idx]), 2),
                    "mean": round(float(mean), 2),
                    "z_score": round(float(z_scores[worst_idx]), 2),
                    "timestamp": svc_df.iloc[worst_idx]["timestamp"]
                })

print("✅ Extended telemetry finalizer ready.")

# ── Register all nodes ────────────────────────────────────────────────────────
graph.add_node("router_node",          router_node)
graph.add_node("analytics_node",       analytics_node)
graph.add_node("rag_node",             rag_node)
graph.add_node("forecasting_node",     forecasting_node)
graph.add_node("anomaly_node",         anomaly_node)
graph.add_node("general_node",         general_node)
graph.add_node("investor_agent_node",  investor_agent_node)
graph.add_node("ecosystem_agent_node", ecosystem_agent_node)
graph.add_node("critic_node",          critic_node)
graph.add_node("telemetry_node",       telemetry_node)

# ── All agents → critic → telemetry → END ─────────────────────────────────────
ALL_AGENTS = [
    "analytics_node","rag_node","forecasting_node","anomaly_node",
    "general_node","investor_agent_node","ecosystem_agent_node"
]
for agent in ALL_AGENTS:
    graph.add_edge(agent, "critic_node")

graph.add_edge("critic_node",   "telemetry_node")
graph.add_edge("telemetry_node", END)

platform = graph.compile(checkpointer=checkpointer)
print("✅ ARIA Enterprise Intelligence Graph compiled.")
print(f"   Nodes: router | analytics | rag | forecasting | anomaly | investor | ecosystem | critic | telemetry")
print(f"   Routes: analytics | rag | forecasting | anomaly | investor | ecosystem | general")


def run_evaluation(test_suite: list = None) -> tuple:
    """Run the benchmark test suite and compute aggregate metrics."""
    if test_suite is None:
        test_suite = QUERY_TEST_SUITE
    results = []
    print(f"🧪 Running {len(test_suite)} evaluation queries...")
    for test in test_suite:
        start = time.time()
        try:
            output = platform.invoke(
                {"messages": [HumanMessage(content=test["query"])]},
                config={"configurable": {"thread_id": test["id"]}}
            )
            latency_ms = (time.time() - start) * 1000
            actual_route = output.get("route","unknown")
            sql_error = str(output.get("sql_result","") or "").startswith("SQL ERROR")
            results.append({
                "test_id": test["id"],
                "query": test["query"][:60],
                "expected_route": test.get("expected_route","any"),
                "actual_route": actual_route,
                "route_correct": (test.get("expected_route","") == actual_route),
                "sql_success": not sql_error,
                "sql_retries": output.get("sql_retry_count", 0) or 0,
                "validator_passed": output.get("validator_passed", True),
                "confidence_score": round(output.get("confidence_score", 0.8) or 0.8, 3),
                "latency_ms": round(latency_ms, 1),
                "sources_cited": len(output.get("sources",[]) or []),
                "error": None,
            })
            print(f"  [{actual_route.upper():<12}] {test['id']:<12} {latency_ms:.0f}ms "
                  f"{'✅' if results[-1]['route_correct'] else '❌'}")
        except Exception as e:
            results.append({"test_id": test["id"], "query": test["query"][:60],
                            "error": str(e), "latency_ms": 0, "route_correct": False,
                            "sql_success": False, "sql_retries": 0, "validator_passed": False,
                            "confidence_score": 0.0, "sources_cited": 0,
                            "expected_route": test.get("expected_route",""), "actual_route": "error"})
            print(f"  [ERROR     ] {test['id']} — {e}")

    df = pd.DataFrame(results)
    metrics = {}
    for col, label in [
        ("route_correct",    "routing_accuracy"),
        ("sql_success",      "sql_execution_success_rate"),
        ("validator_passed", "validator_pass_rate"),
        ("confidence_score", "avg_confidence"),
    ]:
        if col in df.columns:
            metrics[label] = round(df[col].mean(), 3)
    if "sql_retries" in df.columns:
        metrics["avg_sql_retry_count"] = round(df["sql_retries"].mean(), 3)
    if "latency_ms" in df.columns:
        metrics["p50_latency_ms"] = round(df["latency_ms"].quantile(0.50), 1)
        metrics["p95_latency_ms"] = round(df["latency_ms"].quantile(0.95), 1)
    if "sources_cited" in df.columns:
        metrics["avg_sources_per_response"] = round(df["sources_cited"].mean(), 2)


eval_df, eval_metrics = run_evaluation(QUERY_TEST_SUITE[:6])  # Run subset for speed
print("\n✅ Evaluation complete.")
print(eval_df[["test_id","expected_route","actual_route","route_correct","latency_ms"]].to_string(index=False))

def build_telemetry_chart():
    df = get_telemetry_df()
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title="No telemetry yet — run some queries!", template="plotly_dark")
        return fig
    fig = px.scatter(df, x="timestamp", y="total_latency_ms", color="route",
                     size="estimated_tokens", title="Request Latency by Route",
                     template="plotly_dark",
                     hover_data=["confidence_score","validator_passed","query","sql_retry_count"])
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

def build_route_pie():
    df = get_telemetry_df()
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title="No data yet", template="plotly_dark")
        return fig
    route_counts = df["route"].value_counts().reset_index()
    route_counts.columns = ["route","count"]
    fig = px.pie(route_counts, values="count", names="route",
                 title="Route Distribution", template="plotly_dark",
                 color_discrete_sequence=px.colors.sequential.Teal)
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)")
    return fig

def build_retry_chart():
    """Show SQL retry counts per route."""
    df = get_telemetry_df()
    if df.empty or "sql_retry_count" not in df.columns:
        return go.Figure().update_layout(title="No retry data yet", template="plotly_dark")
    retry_df = df.groupby("route")["sql_retry_count"].mean().reset_index()
    fig = px.bar(retry_df, x="route", y="sql_retry_count",
                 title="Avg SQL Retries by Route", template="plotly_dark",
                 color="sql_retry_count", color_continuous_scale="Reds")
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

def refresh_telemetry():
    df = get_telemetry_df()
    if df.empty:
        return "No telemetry yet.", build_telemetry_chart(), build_route_pie(), build_retry_chart()
    cols = ["timestamp","route","total_latency_ms","confidence_score",
            "validator_passed","sql_retry_count","db_queried","query"]
    available = [c for c in cols if c in df.columns]
    summary = df[available].tail(10).to_string(index=False)
    return summary, build_telemetry_chart(), build_route_pie(), build_retry_chart()

        # ── Tab 5: Observability & Telemetry ──────────────────────────────────
        with gr.Tab("🔬 Observability & Telemetry"):
            gr.Markdown("### Production Telemetry — Latency · Confidence · Route · Retries · DB")
            with gr.Row():
                latency_plot  = gr.Plot(label="Latency by Route")
                route_plot    = gr.Plot(label="Route Distribution")
            retry_plot    = gr.Plot(label="Avg SQL Retries by Route")
            telemetry_table = gr.Textbox(label="Recent Requests (last 10)", lines=12, interactive=False)
            refresh_telem_btn = gr.Button("🔄 Refresh Telemetry")
            refresh_telem_btn.click(
                fn=refresh_telemetry,
                outputs=[telemetry_table, latency_plot, route_plot, retry_plot]
            )


# ── Pre-warm with sample queries so telemetry panel has data ──────────────────
print("🔥 Pre-warming ARIA with sample queries...")
warmup_queries = [
    ("Which country has the highest average startup valuation?",   "analytics"),
    ("What are the best practices for RAG architecture?",          "rag"),
    ("Are there any anomalies in the ML Inference service?",       "anomaly"),
    ("Which VC funds raised the most capital?",                    "investor"),
    ("What sectors have the highest acquisition exit rates?",      "ecosystem"),
]
for q, expected_route in warmup_queries:
    r = query_platform(q, thread_id="warmup")
    print(f"  [{expected_route.upper():<12}] ✅ done")

print(f"\n📈 Telemetry records loaded: {len(telemetry_log)}")
print("\n" + "="*65)
print("🚀 LAUNCHING ARIA ENTERPRISE INTELLIGENCE DASHBOARD")
print("="*65)

def planner_node(state: StrategicState) -> StrategicState:
    """Decompose the strategic query into executable subtasks."""
    t0 = time.time()
    query = state["messages"][-1].content
    trace = state.get("execution_trace") or []

    trace.append({
        "agent": "Planner",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "action": f"Decomposing query: {query[:80]}..."
    })

    trace.append({
        "agent": "Planner",
        "status": "complete",
        "timestamp": datetime.now().isoformat(),
        "action": f"Plan ready: {len(plan.get('subtasks',[]))} subtasks | complexity: {plan.get('complexity','?')}",
        "output_preview": json.dumps(plan.get("subtasks",[])[:2])[:200]
    })

def market_analyst_node(state: StrategicState) -> StrategicState:
    """Run SWOT + TAM/SAM/SOM + trend analysis."""
    query = state.get("strategic_query") or state["messages"][-1].content
    trace = state.get("execution_trace") or []
    critique_log = state.get("critique_log") or []

    trace.append({
        "agent": "MarketAnalyst",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "action": "Retrieving market intelligence..."
    })

    trace.append({
        "agent": "MarketAnalyst",
        "status": "complete",
        "timestamp": datetime.now().isoformat(),
        "action": f"Market analysis complete | confidence: {confidence:.2f} | TAM: ${analysis.get('tam_usd_bn','?')}B",
        "output_preview": analysis.get("market_overview","")[:150]
    })

    # ── Retrieve for each subtask ────────────────────────────────────────────
    t_ret = time.time()
    all_docs = {}
    for task in subtasks[:4]:  # Cap at 4 to keep latency reasonable
        task_query = f"{task.get('type','')} {task.get('question', active_query)}"
        docs = hybrid_retrieve(task_query, top_k=3)
        all_docs[task["id"]] = [
            {"content": d.page_content[:250], "source": d.metadata.get("source","kb"), "type": d.metadata.get("type","?")}
            for d in docs
        ]

    trace.append({
        "agent": "CriticValidator",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "action": f"Validating analysis | evidence quality: {evidence_quality:.2f}"
    })

    trace.append({
        "agent": "CriticValidator",
        "status": "retry_triggered" if retry_needed else ("failed" if not passed else "passed"),
        "timestamp": datetime.now().isoformat(),
        "action": (f"🔄 RETRY triggered: {verdict.get('retry_reason','low confidence')}"
                   if retry_needed else
                   f"{'✅ PASSED' if passed else '⚠️ FAILED'}: {verdict.get('verdict','')}"),
        "output_preview": f"conf={final_confidence:.2f} | risk={verdict.get('hallucination_risk')} | retry={retry_needed}"
    })

    return {
        **state,
        "validator_passed": passed and not retry_needed,
        "confidence_score": final_confidence,
        "evidence_quality": float(verdict.get("evidence_quality_score", evidence_quality)),
        "retry_reason": verdict.get("retry_reason") if retry_needed else None,
        "critique_log": critique_log,
        "execution_trace": trace,
    }

def report_generator_node(state: StrategicState) -> StrategicState:
    """Generate the final executive intelligence report."""
    query = state.get("strategic_query") or state["messages"][-1].content
    market_analysis = state.get("market_analysis") or {}
    swot = state.get("swot") or {}
    evidence_quality = state.get("evidence_quality") or 0.0
    confidence = state.get("confidence_score") or 0.75
    sources = state.get("sources") or {}
    critique_log = state.get("critique_log") or []
    trace = state.get("execution_trace") or []

    trace.append({
        "agent": "ReportGenerator",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "action": "Synthesizing executive intelligence report..."
    })

    trace.append({
        "agent": "ReportGenerator",
        "status": "complete",
        "timestamp": datetime.now().isoformat(),
        "action": f"Report generated | {len(report_text)} chars | confidence: {report_confidence:.0%}",
        "output_preview": report_text[:200]
    })

    print(f"📋 ReportGenerator | {len(report_text)} chars | conf: {report_confidence:.0%} | {len(trace)} trace steps")
    return {{
        **state,
        "messages": [*state["messages"], response.__class__(content=final_message)],
        "final_report": report_text,
        "report_confidence": report_confidence,
        "execution_trace": trace,
    }}

strategic_graph.add_edge("report_generator_node", "telemetry_node")
strategic_graph.add_edge("telemetry_node",         END)


def run_strategic_analysis(query: str, thread_id: str = "strategic_default") -> dict:
    """
    Run a full strategic intelligence analysis.
    Returns: {'report': str, 'trace': list, 'confidence': float, 'critique_log': list}
    """
    config = {"configurable": {"thread_id": thread_id}}
    result = strategic_platform.invoke(
        {"messages": [HumanMessage(content=query)]},
        config=config
    )

# ── State storage for live trace display ──────────────────────────────────────
_live_state = {"running": False, "result": None, "trace_text": ""}

def _run_analysis_async(query: str):
    _live_state["running"] = True
    _live_state["result"] = None
    _live_state["trace_text"] = ""
    try:
        r = run_strategic_analysis(query, thread_id=f"sos_{uuid.uuid4().hex[:6]}")
        _live_state["result"] = r
        _live_state["trace_text"] = format_trace(r["trace"])
    except Exception as e:
        _live_state["result"] = {"error": str(e)}
    finally:
        _live_state["running"] = False

def format_trace(trace: list) -> str:
    lines = []
    for step in trace:
        agent = step.get("agent","?")
        status = step.get("status","?")
        ts = step.get("timestamp","?")[:19]
        action = step.get("action","")
        preview = step.get("output_preview","")
        status_icon = {
            "running":         "🔄",
            "complete":        "✅",
            "passed":          "✅",
            "failed":          "⚠️",
            "retry_triggered": "🔁",
            "rewriting":       "✏️",
        }.get(status, "•")
        line = f"{status_icon} [{ts}] {agent:<22} | {status:<18} | {action}"
        if preview:
            line += f"\n    └─ {preview[:120]}"
        lines.append(line)
    return "\n".join(lines)

        # ═══ PAGE 2: Live Agent Orchestration ══════════════════════════════════
        with gr.Tab("⚙️ Agent Orchestration"):
            gr.Markdown("### Live Agent Execution Trace")
            with gr.Row():
                with gr.Column(scale=2):
                    trace_output = gr.Textbox(
                        label="Execution Trace — Live Agent Steps",
                        lines=20, interactive=False,
                        value="Run an analysis to see the live execution trace here..."
                    )
                with gr.Column(scale=1):
                    gr.Markdown("#### 🔁 Self-Correction Log")
                    critique_output = gr.Textbox(
                        label="Query Rewrites & Validation Events",
                        lines=20, interactive=False,
                        value="Self-correction events will appear here..."
                    )
            refresh_trace_btn = gr.Button("🔄 Refresh Trace")

        # ═══ PAGE 4: Reliability & Telemetry ═══════════════════════════════════
        with gr.Tab("🔬 Reliability & Telemetry"):
            gr.Markdown("### Production Telemetry — ARIA + Strategic OS")
            with gr.Row():
                latency_chart   = gr.Plot(label="Latency by Route")
                route_chart     = gr.Plot(label="Route Distribution")
            retry_chart     = gr.Plot(label="SQL Retry Distribution")
            gr.Markdown("#### Recent Requests")
            telem_table = gr.Textbox(label="Telemetry Log", lines=12, interactive=False)
            refresh_telem = gr.Button("🔄 Refresh Telemetry")

            refresh_telem.click(
                fn=refresh_telemetry,
                outputs=[telem_table, latency_chart, route_chart, retry_chart]
            )

    def get_trace_from_state(result):
        if result is None:
            return "No analysis run yet.", "No self-corrections yet."
        trace = result.get("trace") or []
        critique = result.get("critique_log") or []
        return format_trace(trace), format_critique_log(critique)

    refresh_trace_btn.click(
        fn=get_trace_from_state,
        inputs=[current_result],
        outputs=[trace_output, critique_output]
    )

    report_output.change(
        fn=get_trace_from_state,
        inputs=[current_result],
        outputs=[trace_output, critique_output]
    )

print("\n✅ Strategic Intelligence OS Dashboard defined — 4 pages.")
print("   Page 1: Executive Intelligence  (query + KPI cards + market overview)")
print("   Page 2: Agent Orchestration     (live trace + self-correction log)")
print("   Page 3: Intelligence Report     (full executive report + export)")
print("   Page 4: Reliability & Telemetry (latency + routes + retry distribution)")