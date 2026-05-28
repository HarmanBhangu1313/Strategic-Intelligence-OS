"""
Auto-extracted from ARIA_Strategic_Intelligence_OS.ipynb
"""

    """Sales pipeline analytics: Win rate by stage shows qualification effectiveness. Average deal
    size by region identifies geographic opportunities. Pipeline velocity is the key metric for
    revenue forecasting. CRM data quality directly impacts forecast accuracy.""",
]

- analytics  : SQL-answerable questions about structured data (funding, sales, KPIs, rankings, totals)
- rag        : Semantic search questions about knowledge base / company documents
- forecasting: Trend prediction, growth projection, time-series extrapolation
- anomaly    : Detecting outliers, spikes, failures, unusual patterns
- investor   : VC/investor analysis, fund sizes, investment patterns, which VCs to watch
- ecosystem  : Startup sector trends, geographic distribution, market analysis, exit rates
- general    : Conversation, greetings, out-of-scope questions

VALID_ROUTES = {"analytics","rag","forecasting","anomaly","investor","ecosystem","general"}


def route_selector_v2(state: EnterpriseState):
    mapping = {
        "analytics":  "analytics_node",
        "rag":        "rag_node",
        "forecasting":"forecasting_node",
        "anomaly":    "anomaly_node",
        "investor":   "investor_agent_node",
        "ecosystem":  "ecosystem_agent_node",
        "general":    "general_node",
    }
    return mapping.get(state["route"], "general_node")


def forecast_funding_trends(sector_filter: str = None) -> str:
    """Sector-level funding trajectory analysis from Crunchbase data."""
    conn = sqlite3.connect(CB_DB_PATH)
    q = """
        SELECT strftime('%Y', first_funding_at) as year, category_code,
               COUNT(*) as companies_funded,
               SUM(funding_total_usd) as total_funding_usd,
               AVG(funding_total_usd) as avg_funding_usd
        FROM cb_objects
        WHERE entity_type='Company' AND first_funding_at IS NOT NULL
          AND first_funding_at != '' AND funding_total_usd > 0
    """
    if sector_filter:
        q += f" AND category_code = '{sector_filter}'"
    q += " GROUP BY year, category_code ORDER BY year"
    df = pd.read_sql_query(q, conn)
    conn.close()


def forecasting_node(state: EnterpriseState) -> EnterpriseState:
    """Product KPI forecasting + Crunchbase funding trend forecasting."""
    query = state["messages"][-1].content
    t_sql = time.time()

    # ── KPI trend from enterprise DB ─────────────────────────────────────────
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT date, product, SUM(revenue) as total_revenue, AVG(dau) as avg_dau,
               AVG(churn_rate) as avg_churn
        FROM product_kpis GROUP BY date, product ORDER BY date
    """, conn)
    conn.close()
    sql_ms = (time.time() - t_sql) * 1000

    kpi_summary = []
    for product in df["product"].unique():
        pdata = df[df["product"] == product].copy()
        pdata["t"] = range(len(pdata))
        if len(pdata) < 4:
            continue
        coeffs = np.polyfit(pdata["t"], pdata["total_revenue"], 1)
        slope = coeffs[0]
        next_4_weeks = [coeffs[0]*(len(pdata)+i)+coeffs[1] for i in range(1, 5)]
        kpi_summary.append(
            f"**{product}**: {'📈' if slope>0 else '📉'} (slope: ${slope:+.0f}/wk). "
            f"4-week forecast: ${next_4_weeks[-1]:,.0f}"
        )

    # ── Funding trend from Crunchbase ─────────────────────────────────────────
    funding_trends = forecast_funding_trends()

    forecast_prompt = f"""You are a business forecasting analyst.

Product KPI Trends:
{'\n'.join(kpi_summary)}

Crunchbase Startup Funding Trends (by sector):
{funding_trends}

Provide an executive forecast summary:
1. Overall product revenue trajectory
2. Best/worst KPI momentum product
3. Top 3 sectors showing accelerating funding
4. Risk factors and recommended leadership actions
"""
    response = llm.invoke([HumanMessage(content=forecast_prompt)])
    final = f"📈 **Forecasting Analysis**\n\n{response.content}\n\n---\n*Sources: product_kpis + crunchbase_ecosystem | SQL: {sql_ms:.1f}ms*"
    return {
        **state,
        "messages": [*state["messages"], response.__class__(content=final)],
        "sql_ms": sql_ms,
        "confidence_score": 0.74,
        "sources": ["product_kpis","crunchbase_ecosystem"],
    }

print("✅ Forecasting agent ready (KPI + CB funding trends).")


def ecosystem_agent_node(state: EnterpriseState) -> EnterpriseState:
    """
    Handles broad ecosystem questions: sector analysis, geographic trends,
    startup status distributions, and acquisition/IPO exit rate analysis.
    """
    query = state["messages"][-1].content


def general_node(state: EnterpriseState) -> EnterpriseState:
    """Fallback for greetings and out-of-scope queries."""
    system = SystemMessage(content="""You are ARIA — an Enterprise Decision Intelligence assistant.
You help analysts, executives, and data teams query enterprise and startup ecosystem data,
detect anomalies, generate forecasts, and retrieve business knowledge.
You have access to:
- Operational enterprise data (startup funding, sales pipeline, product KPIs, ops metrics)
- Crunchbase startup ecosystem (companies, investors, acquisitions, IPOs, people, milestones)
""")
    messages = [system] + list(state["messages"])
    response = llm.invoke(messages)
    return {
        **state,
        "messages": [*state["messages"], response],
        "confidence_score": 0.95,
        "sources": [],
    }

# ── Conditional dispatch ───────────────────────────────────────────────────────
graph.add_conditional_edges(
    "router_node",
    route_selector_v2,
    {
        "analytics_node":      "analytics_node",
        "rag_node":            "rag_node",
        "forecasting_node":    "forecasting_node",
        "anomaly_node":        "anomaly_node",
        "investor_agent_node": "investor_agent_node",
        "ecosystem_agent_node":"ecosystem_agent_node",
        "general_node":        "general_node",
    }
)

smoke_tests = [
    ("Which sector raised the most total funding?",          "analytics"),
    ("What are the best practices for RAG architecture?",    "rag"),
    ("Forecast revenue trends for our products",             "forecasting"),
    ("Are there anomalies in our operational metrics?",      "anomaly"),
    ("Which VC funds raised the most capital?",              "investor"),
    ("What sectors have the highest acquisition exit rate?", "ecosystem"),
]
for q, expected in smoke_tests:
    print(f"\n❓ [{expected.upper()}] {q}")
    print("-" * 55)
    resp = query_platform(q, thread_id="smoke_test")
    print(resp[:250], "...")


QUERY_TEST_SUITE = [
    # Text-to-SQL — enterprise DB
    {"id":"sql-01","query":"Which sector raised the most total funding?",
     "expected_route":"analytics","check":"contains_number"},
    {"id":"sql-02","query":"What is the average deal value by sales region?",
     "expected_route":"analytics","check":"contains_number"},
    {"id":"sql-03","query":"Which product has the highest average DAU?",
     "expected_route":"analytics","check":"contains_number"},
    # Text-to-SQL — Crunchbase
    {"id":"sql-04","query":"Top 10 companies by total funding in the AI sector",
     "expected_route":"analytics","check":"contains_number"},
    {"id":"sql-05","query":"Which acquirers completed the most deals post-2010?",
     "expected_route":"analytics","check":"contains_number"},
    {"id":"sql-06","query":"IPO companies with highest valuations",
     "expected_route":"analytics","check":"contains_number"},
    # Routing accuracy
    {"id":"route-01","query":"Tell me about Y Combinator and its portfolio",
     "expected_route":"rag"},
    {"id":"route-02","query":"Which VC raised the most capital?",
     "expected_route":"investor"},
    {"id":"route-03","query":"Detect unusual funding patterns in biotech",
     "expected_route":"anomaly"},
    {"id":"route-04","query":"What sectors have the highest IPO exit rates?",
     "expected_route":"ecosystem"},
    {"id":"route-05","query":"Forecast startup funding trends for next year",
     "expected_route":"forecasting"},
    # RAG grounding
    {"id":"rag-01","query":"What are best practices for LangGraph multi-agent systems?",
     "expected_route":"rag"},
    {"id":"rag-02","query":"What does enterprise AI adoption look like in 2024?",
     "expected_route":"rag"},
    # Investor
    {"id":"inv-01","query":"Compare fund sizes across top-tier VCs",
     "expected_route":"investor"},
    # Ecosystem
    {"id":"eco-01","query":"What is the geographic distribution of funded startups?",
     "expected_route":"ecosystem"},
]

def build_kpi_chart():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT date, product, SUM(revenue) as revenue
        FROM product_kpis GROUP BY date, product ORDER BY date
    """, conn)
    conn.close()
    fig = px.line(df, x="date", y="revenue", color="product",
                  title="Product Revenue Trend (Weekly)", template="plotly_dark",
                  color_discrete_sequence=["#00d4ff","#7c3aed","#10b981"])
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

        # ── Tab 1: Intelligence Chat ──────────────────────────────────────────
        with gr.Tab("🤖 Intelligence Chat"):
            gr.Markdown("### Ask anything about enterprise or startup ecosystem data")
            gr.Markdown(
                "**Try:**\n"
                "- *'Which sector raised the most funding?'*\n"
                "- *'Which VC funds raised the most capital?'*\n"
                "- *'What sectors have the highest acquisition exit rates?'*\n"
                "- *'Are there any anomalies in our operational metrics?'*\n"
                "- *'Forecast startup funding trends'*"
            )
            gr.ChatInterface(
                fn=chat_fn,
                type="messages",
                examples=[
                    "Which startup raised the most funding?",
                    "Which VC raised the most capital?",
                    "What sectors have the highest IPO exit rates?",
                    "Detect anomalies in funding and operational data",
                    "Forecast product revenue and startup funding trends",
                    "What are best practices for RAG architecture?",
                ]
            )

        # ── Tab 2: Analytics Dashboard ────────────────────────────────────────
        with gr.Tab("📊 Analytics Dashboard"):
            gr.Markdown("### Enterprise KPI Visualizations")
            with gr.Row():
                kpi_plot      = gr.Plot(value=build_kpi_chart,      label="Revenue Trend")
                funding_plot  = gr.Plot(value=build_funding_chart,  label="Funding by Sector")
            with gr.Row():
                pipeline_plot = gr.Plot(value=build_pipeline_chart, label="Sales Pipeline")
            refresh_btn = gr.Button("🔄 Refresh Charts")
            refresh_btn.click(
                fn=lambda: (build_kpi_chart(), build_funding_chart(), build_pipeline_chart()),
                outputs=[kpi_plot, funding_plot, pipeline_plot]
            )

        # ── Tab 4: Acquisition Intelligence ──────────────────────────────────
        with gr.Tab("🤝 Acquisition Intelligence"):
            gr.Markdown("## M&A Trend Analysis")
            run_acq_btn   = gr.Button("📊 Load Acquisition Data")
            acq_table     = gr.DataFrame(label="Top Acquirers by Deal Count")
            anomaly_table = gr.DataFrame(label="Anomalous Acquirers (Deal Velocity Z > 2.0)")
            funding_anom  = gr.DataFrame(label="Funding Anomalies (Sector Peer Z > 3.0)")
            run_acq_btn.click(
                fn=lambda: (*load_acquisition_data(), load_funding_anomalies()),
                outputs=[acq_table, anomaly_table, funding_anom]
            )

    try:
        clean = re.sub(r"```json|```", "", resp.content.strip()).strip()
        plan = json.loads(clean)
    except Exception:
        plan = {
            "query_intent": query[:100],
            "complexity": "medium",
            "subtasks": [
                {"id": "t1", "type": "market_analysis",      "question": f"Market size and trends for: {query}", "priority": 1},
                {"id": "t2", "type": "competitor_research",  "question": f"Key competitors in: {query}",         "priority": 2},
                {"id": "t3", "type": "risk_assessment",      "question": f"Major risks for: {query}",            "priority": 3},
                {"id": "t4", "type": "opportunity_detection","question": f"Growth opportunities in: {query}",    "priority": 4},
            ],
            "key_uncertainties": ["Market data recency", "Competitor data completeness"]
        }


MARKET_ANALYST_SYSTEM = """You are an elite Market Intelligence Analyst.
You produce executive-grade strategic analysis including SWOT, market sizing, trend analysis, and competitor mapping.

Given a strategic query, produce a comprehensive market analysis in JSON:
{
  "market_overview": "2-3 sentence summary",
  "tam_usd_bn": <number>,
  "sam_usd_bn": <number>,
  "som_usd_bn": <number>,
  "growth_rate_pct": <number>,
  "swot": {
    "strengths": ["...", "..."],
    "weaknesses": ["...", "..."],
    "opportunities": ["...", "..."],
    "threats": ["...", "..."]
  },
  "key_trends": ["...", "..."],
  "market_maturity": "emerging|growing|mature|declining",
  "competitive_intensity": "low|medium|high|very_high",
  "confidence_score": 0.0-1.0,
  "evidence_sources": ["..."]
}

    # SQL: sector funding trends as market signal
    sector_sql = """
        SELECT sector, SUM(amount_usd)/1e6 as total_funding_m,
               COUNT(*) as deals, AVG(amount_usd)/1e6 as avg_deal_m
        FROM startup_funding GROUP BY sector ORDER BY total_funding_m DESC
    """
    sql_data, sql_ms = execute_sql_safely_v2(sector_sql)

    try:
        clean = re.sub(r"```json|```", "", resp.content.strip()).strip()
        analysis = json.loads(clean)
    except Exception:
        analysis = {
            "market_overview": resp.content[:300],
            "tam_usd_bn": None, "sam_usd_bn": None, "som_usd_bn": None,
            "growth_rate_pct": None,
            "swot": {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []},
            "key_trends": [], "market_maturity": "unknown",
            "competitive_intensity": "medium",
            "confidence_score": 0.55,
            "evidence_sources": [d.metadata.get("source","kb") for d in market_docs]
        }

### 2.3 Key Market Trends
1. [Trend 1 + evidence]
2. [Trend 2 + evidence]
3. [Trend 3 + evidence]

Market Analysis Results:
- Overview: {market_analysis.get('market_overview','Not available')}
- TAM: ${market_analysis.get('tam_usd_bn','?')}B | SAM: ${market_analysis.get('sam_usd_bn','?')}B | SOM: ${market_analysis.get('som_usd_bn','?')}B
- Growth Rate: {market_analysis.get('growth_rate_pct','?')}%
- Market Maturity: {market_analysis.get('market_maturity','?')}
- Competitive Intensity: {market_analysis.get('competitive_intensity','?')}
- Key Trends: {market_analysis.get('key_trends',[])}

def build_evidence_chart(market_analysis: dict) -> object:
    cats = ["TAM Estimate","SAM Estimate","SOM Estimate","SWOT Coverage","Trend Data","Competitor Intel"]
    ma = market_analysis or {}
    values = [
        70 if ma.get("tam_usd_bn") else 25,
        70 if ma.get("sam_usd_bn") else 25,
        60 if ma.get("som_usd_bn") else 20,
        80 if ma.get("swot",{}).get("strengths") else 30,
        75 if ma.get("key_trends") else 30,
        65 if ma.get("competitive_intensity") else 20,
    ]
    fig = go.Figure(go.Bar(
        x=values, y=cats, orientation="h",
        marker_color=["#0ea5e9","#6366f1","#8b5cf6","#10b981","#f59e0b","#ec4899"],
        marker_line_width=0,
    ))
    fig.update_layout(
        title={"text":"Evidence Coverage by Category","font":{"color":"#94a3b8","size":13}},
        paper_bgcolor="#04040c", plot_bgcolor="#0d1424",
        font_color="#e2e8f0", height=220,
        xaxis=dict(range=[0,100], ticksuffix="%", gridcolor="#1e2d4a"),
        yaxis=dict(gridcolor="#1e2d4a"),
        margin=dict(l=10,r=10,t=40,b=10)
    )
    return fig

        market_text = (
            f"Overview:  {ma.get('market_overview','N/A')}\n\n"
            f"TAM: ${ma.get('tam_usd_bn','?')}B | SAM: ${ma.get('sam_usd_bn','?')}B | SOM: ${ma.get('som_usd_bn','?')}B\n"
            f"Growth: {ma.get('growth_rate_pct','?')}% CAGR | Maturity: {ma.get('market_maturity','?')}\n\n"
            f"Key Trends:\n" + "\n".join(f"• {t}" for t in (ma.get('key_trends') or [])[:4])
        )