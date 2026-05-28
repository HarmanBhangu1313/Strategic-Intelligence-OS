"""
Auto-extracted from ARIA_Strategic_Intelligence_OS.ipynb
"""

# ── Structured / Analytics ────────────────────────────────────────────────────
import sqlite3
import pandas as pd
import numpy as np
import json, time, uuid, re, os
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from collections import defaultdict
from pathlib import Path

def build_enterprise_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()


def build_crunchbase_schema(conn: sqlite3.Connection):
    """Create all 9 Crunchbase tables plus placeholder tables for future data."""
    cur = conn.cursor()
    cur.executescript("""
    PRAGMA foreign_keys = ON;
    PRAGMA journal_mode = WAL;
    PRAGMA synchronous = NORMAL;


def build_indexes(conn: sqlite3.Connection):
    """Build 18 performance indexes across all Crunchbase tables."""
    cur = conn.cursor()
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_obj_entity_type ON cb_objects(entity_type)",
        "CREATE INDEX IF NOT EXISTS idx_obj_category    ON cb_objects(category_code)",
        "CREATE INDEX IF NOT EXISTS idx_obj_status      ON cb_objects(status)",
        "CREATE INDEX IF NOT EXISTS idx_obj_country     ON cb_objects(country_code)",
        "CREATE INDEX IF NOT EXISTS idx_obj_founded     ON cb_objects(founded_at)",
        "CREATE INDEX IF NOT EXISTS idx_obj_funding     ON cb_objects(funding_total_usd)",
        "CREATE INDEX IF NOT EXISTS idx_acq_acquirer    ON cb_acquisitions(acquiring_object_id)",
        "CREATE INDEX IF NOT EXISTS idx_acq_acquired    ON cb_acquisitions(acquired_object_id)",
        "CREATE INDEX IF NOT EXISTS idx_acq_date        ON cb_acquisitions(acquired_at)",
        "CREATE INDEX IF NOT EXISTS idx_ipo_obj         ON cb_ipos(object_id)",
        "CREATE INDEX IF NOT EXISTS idx_ipo_date        ON cb_ipos(public_at)",
        "CREATE INDEX IF NOT EXISTS idx_rel_person      ON cb_relationships(person_object_id)",
        "CREATE INDEX IF NOT EXISTS idx_rel_company     ON cb_relationships(relationship_object_id)",
        "CREATE INDEX IF NOT EXISTS idx_rel_role        ON cb_relationships(role_category)",
        "CREATE INDEX IF NOT EXISTS idx_off_obj         ON cb_offices(object_id)",
        "CREATE INDEX IF NOT EXISTS idx_off_country     ON cb_offices(country_code)",
        "CREATE INDEX IF NOT EXISTS idx_mil_obj         ON cb_milestones(object_id)",
        "CREATE INDEX IF NOT EXISTS idx_funds_obj       ON cb_funds(object_id)",
    ]
    for idx in indexes:
        cur.execute(idx)
    conn.commit()
    print(f"  ✅ {len(indexes)} indexes created")


def load_csv_chunked(conn, csv_path: Path, table_name: str, chunk_size: int = 50_000):
    """Load a cleaned CSV into SQLite in chunks (handles 1M+ rows)."""
    total = 0
    try:
        for chunk in pd.read_csv(csv_path, chunksize=chunk_size, low_memory=False):
            # Drop columns that don't exist in target table
            chunk.to_sql(table_name, conn, if_exists="append", index=False, method="multi")
            total += len(chunk)
        print(f"  Loaded {total:,} rows → {table_name}")
    except Exception as e:
        print(f"  ⚠️  Error loading {table_name}: {e}")
    return total


def build_crunchbase_db():
    """Assemble the complete Crunchbase relational database."""
    conn = sqlite3.connect(CB_DB_PATH)


def get_db_schema() -> str:
    """Return schema string for the enterprise operational DB."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    parts = []
    for table in tables:
        cur.execute(f"PRAGMA table_info({table})")
        cols = cur.fetchall()
        col_defs = ", ".join(f"{c[1]} ({c[2]})" for c in cols)
        cur.execute(f"SELECT * FROM {table} LIMIT 2")
        sample = cur.fetchall()
        parts.append(f"TABLE: {table}\n  COLUMNS: {col_defs}\n  SAMPLE: {sample}")
    conn.close()
    return "\n\n".join(parts)


def get_cb_schema() -> str:
    """Return schema string for Crunchbase DB with join hints."""
    conn = sqlite3.connect(CB_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    parts = [CB_RELATIONSHIP_MAP]
    for table in tables:
        cur.execute(f"PRAGMA table_info({table})")
        cols = cur.fetchall()
        col_defs = ", ".join(f"{c[1]} ({c[2]})" for c in cols)
        cur.execute(f"SELECT * FROM {table} LIMIT 1")
        sample = cur.fetchall()
        parts.append(f"TABLE: {table}\n  COLUMNS: {col_defs}\n  SAMPLE: {sample}")
    conn.close()
    return "\n\n".join(parts)


# Save machine-readable registry
schema_registry = {
    "databases": {
        "enterprise_intelligence": {
            "path": DB_PATH,
            "tables": ["startup_funding","sales_pipeline","product_kpis","operational_metrics"],
            "primary_use": "operational analytics, KPI tracking"
        },
        "crunchbase_ecosystem": {
            "path": CB_DB_PATH,
            "tables": ["cb_objects","cb_acquisitions","cb_ipos","cb_people",
                       "cb_relationships","cb_offices","cb_milestones","cb_degrees","cb_funds"],
            "primary_use": "startup ecosystem intelligence, investor analysis, M&A"
        }
    },
    "common_joins": [
        {"name":"company_acquisitions",
         "sql":"cb_objects o JOIN cb_acquisitions a ON o.id = a.acquired_object_id"},
        {"name":"company_ipo",
         "sql":"cb_objects o JOIN cb_ipos i ON o.id = i.object_id"},
        {"name":"company_founders",
         "sql":"cb_objects o JOIN cb_relationships r ON o.id = r.relationship_object_id JOIN cb_people p ON p.object_id = r.person_object_id WHERE r.role_category = 'C-Suite/Founder'"},
        {"name":"investor_funds",
         "sql":"cb_objects o JOIN cb_funds f ON o.id = f.object_id WHERE o.entity_type = 'FinancialOrg'"}
    ]
}
with open("config/schema_registry.json","w") as f:
    json.dump(schema_registry, f, indent=2)

    """Text-to-SQL agent design: Schema-aware prompting reduces hallucinated column names by 60%.
    Always include sample rows in the schema context. Use chain-of-thought before generating SQL.
    Validate generated SQL with EXPLAIN before execution. Multi-table queries require explicit JOIN hints.""",


def build_startup_corpus(limit: int = 3000) -> list:
    """Build startup narrative documents from Crunchbase data for RAG indexing."""
    conn = sqlite3.connect(CB_DB_PATH)
    companies = pd.read_sql_query(f"""
        SELECT o.id, o.name, o.category_code, o.status, o.country_code,
               o.founded_at, o.description, o.tag_list, o.funding_total_usd, o.funding_rounds
        FROM cb_objects o
        WHERE o.entity_type = 'Company'
          AND o.description != '' AND o.description IS NOT NULL
        LIMIT {limit}
    """, conn)
    milestones = pd.read_sql_query("""
        SELECT object_id, GROUP_CONCAT(description, '; ') as milestone_text
        FROM cb_milestones WHERE description != ''
        GROUP BY object_id
    """, conn)
    conn.close()


def build_investor_corpus() -> list:
    """Build investor/VC narrative documents."""
    conn = sqlite3.connect(CB_DB_PATH)
    investors = pd.read_sql_query("""
        SELECT o.name, o.description, f.name as fund_name,
               f.raised_amount, f.funded_at
        FROM cb_objects o
        LEFT JOIN cb_funds f ON o.id = f.object_id
        WHERE o.entity_type = 'FinancialOrg'
          AND o.description IS NOT NULL AND o.description != ''
        LIMIT 400
    """, conn)
    conn.close()

print("✅ EnterpriseState schema defined (with sql_retry_count).")

SQL_SYSTEM_PROMPT_V2 = f"""You are an expert enterprise analytics SQL agent with access to TWO SQLite databases.

═══ INSTRUCTIONS ═══
1. Think step-by-step. Identify which database the question touches.
2. For Crunchbase questions, use ONLY cb_* tables.
3. For multi-table Crunchbase queries, use the JOIN MAP above.
4. Write a single valid SQLite query. No markdown. No backticks. No explanation.
5. Always include LIMIT 25 unless the user asks for totals/aggregates.
6. For date arithmetic: strftime('%Y', date_column) to extract year.
7. For anomaly queries: compute AVG and STDEV in a subquery then filter.
8. NEVER hallucinate column names — only use columns from the schema above.
9. Use WITH (CTE) syntax for complex multi-step queries.

═══ EXAMPLE QUERIES ═══
Q: "Top 10 companies by total funding in enterprise software"
SQL:
SELECT name, funding_total_usd, status, country_code
FROM cb_objects
WHERE entity_type='Company' AND category_code='enterprise' AND funding_total_usd > 0
ORDER BY funding_total_usd DESC LIMIT 10;

Q: "Which acquirers did the most deals post-2010?"
SQL:
SELECT o.name, COUNT(*) as deal_count, SUM(a.price_amount) as total_spend_usd
FROM cb_acquisitions a
JOIN cb_objects o ON o.id = a.acquiring_object_id
WHERE a.acquired_at >= '2010-01-01'
GROUP BY o.id, o.name
ORDER BY deal_count DESC LIMIT 15;

Q: "Top sectors by total funding in enterprise DB"
SQL:
SELECT sector, SUM(amount_usd) as total_funding, COUNT(*) as deals
FROM startup_funding
GROUP BY sector ORDER BY total_funding DESC LIMIT 10;
"""


print("✅ SQL engine V2 ready (dual-DB + auto-detect).")


def analytics_node(state: EnterpriseState) -> EnterpriseState:
    """Text-to-SQL with retry correction loop (up to 2 retries)."""
    query = state["messages"][-1].content
    MAX_RETRIES = 2
    generated_sql = None
    result_str = None
    sql_ms = 0.0
    retry_count = 0

    for attempt in range(MAX_RETRIES + 1):
        prompt = query if attempt == 0 else (
            f"{query}\n\nPrevious SQL attempt failed:\n{generated_sql}\n"
            f"Error: {result_str}\nPlease fix the SQL query."
        )
        sql_resp = llm.invoke([
            SystemMessage(content=SQL_SYSTEM_PROMPT_V2),
            HumanMessage(content=prompt)
        ])
        generated_sql = sql_resp.content.strip()
        result_str, sql_ms = execute_sql_safely_v2(generated_sql)
        if not result_str.startswith("SQL ERROR"):
            break
        retry_count += 1
        print(f"  ⚠️  SQL retry {retry_count}/{MAX_RETRIES}")

    formatter_prompt = f"""You are an enterprise BI analyst.
User asked: {query}
SQL: {generated_sql}
Results: {result_str[:1500]}

    db_used = "crunchbase" if any(t in generated_sql for t in CB_TABLES) else "enterprise"
    final = f"""📊 **Analytics Insight**

---
*SQL:* `{generated_sql[:150]}{'...' if len(generated_sql)>150 else ''}`
*Execution:* {sql_ms:.1f}ms | *Retries:* {retry_count} | *DB:* {db_used}
"""
    return {
        **state,
        "messages": [*state["messages"], insight.__class__(content=final)],
        "sql_query": generated_sql,
        "sql_result": result_str,
        "sql_ms": sql_ms,
        "sql_retry_count": retry_count,
        "confidence_score": max(0.5, 0.85 - retry_count * 0.05),
        "sources": [f"{db_used}_db"],
    }


def detect_funding_anomalies() -> list:
    """
    Z-score funding outliers within each sector peer group.
    Peer-group normalization ensures a $500M raise in biotech is judged against biotech peers,
    not the whole market — dramatically reducing false positives.
    """
    conn = sqlite3.connect(CB_DB_PATH)
    df = pd.read_sql_query("""
        SELECT id, name, category_code, funding_total_usd, funding_rounds, founded_at, status
        FROM cb_objects
        WHERE entity_type='Company' AND funding_total_usd > 0 AND category_code != 'unknown'
    """, conn)
    conn.close()


def detect_acquisition_clusters() -> list:
    """Flag acquirers with abnormally high deal velocity (Z > 2.0)."""
    conn = sqlite3.connect(CB_DB_PATH)
    df = pd.read_sql_query("""
        SELECT acquiring_object_id, COUNT(*) as deals,
               MIN(acquired_at) as first_deal, MAX(acquired_at) as last_deal,
               SUM(price_amount) as total_spend
        FROM cb_acquisitions
        WHERE acquired_at IS NOT NULL AND acquired_at != ''
        GROUP BY acquiring_object_id HAVING deals >= 2
        ORDER BY deals DESC LIMIT 50
    """, conn)
    names = pd.read_sql_query(
        "SELECT id, name FROM cb_objects WHERE entity_type IN ('Company','FinancialOrg')", conn
    )
    conn.close()

    # ── Operational anomalies (original) ──────────────────────────────────────
    t_sql = time.time()
    conn = sqlite3.connect(DB_PATH)
    df_ops = pd.read_sql_query("SELECT * FROM operational_metrics", conn)
    conn.close()
    sql_ms = (time.time() - t_sql) * 1000

Provide:
1. Severity assessment per domain (Critical / High / Medium)
2. Most concerning operational signal and root cause hypothesis
3. Most anomalous funding situation and what it could signal
4. Serial acquirer pattern and strategic interpretation
5. Immediate action items
"""
    response = llm.invoke([HumanMessage(content=anomaly_prompt)])
    total_anomalies = len(ops_anomalies) + len(funding_anomalies) + len(acq_clusters)
    final = (f"🚨 **Anomaly Detection Report**\n\n{response.content}\n\n---\n"
             f"*{len(ops_anomalies)} ops | {len(funding_anomalies)} funding | "
             f"{len(acq_clusters)} acquisition cluster anomalies | SQL: {sql_ms:.1f}ms*")
    return {
        **state,
        "messages": [*state["messages"], response.__class__(content=final)],
        "sql_ms": sql_ms,
        "confidence_score": 0.79,
        "sources": ["operational_metrics","crunchbase_ecosystem"],
    }


def investor_agent_node(state: EnterpriseState) -> EnterpriseState:
    """
    Handles VC/investor questions by combining:
    - SQL: structured fund sizes and deal counts from cb_funds + cb_objects
    - RAG: investor narratives from the extended knowledge corpus
    """
    query = state["messages"][-1].content

    # Structured investor metrics
    investor_sql = """
        SELECT o.name, o.status, o.country_code,
               COUNT(f.fund_id) as num_funds,
               SUM(f.raised_amount) as total_raised,
               AVG(f.raised_amount) as avg_fund_size,
               o.description
        FROM cb_objects o
        LEFT JOIN cb_funds f ON o.id = f.object_id
        WHERE o.entity_type = 'FinancialOrg'
        GROUP BY o.id, o.name
        ORDER BY total_raised DESC
        LIMIT 20
    """
    sql_result, sql_ms = execute_sql_safely_v2(investor_sql)

Structured Data (top investors by capital raised):
{sql_result}

    eco_sql = """
        SELECT category_code,
               COUNT(*) as company_count,
               SUM(CASE WHEN status='acquired' THEN 1 ELSE 0 END) as acquisitions,
               SUM(CASE WHEN status='ipo' THEN 1 ELSE 0 END) as ipos,
               SUM(CASE WHEN status='closed' THEN 1 ELSE 0 END) as closures,
               AVG(funding_total_usd) as avg_funding,
               SUM(funding_total_usd) as total_funding
        FROM cb_objects
        WHERE entity_type='Company' AND category_code != 'unknown' AND category_code IS NOT NULL
        GROUP BY category_code
        ORDER BY company_count DESC LIMIT 20
    """
    sql_result, sql_ms = execute_sql_safely_v2(eco_sql)

    # Geographic breakdown
    geo_sql = """
        SELECT country_code, COUNT(*) as companies,
               SUM(funding_total_usd) as total_funding,
               AVG(funding_total_usd) as avg_funding
        FROM cb_objects
        WHERE entity_type='Company' AND country_code != 'UNKNOWN'
        GROUP BY country_code ORDER BY total_funding DESC LIMIT 15
    """
    geo_result, _ = execute_sql_safely_v2(geo_sql)

Sector Data (companies by category):
{sql_result}

Provide:
1. Sector comparison: which sectors lead in volume vs funding
2. Exit rate analysis: acquisition vs IPO vs closure by sector
3. Geographic concentration: dominant hubs and emerging markets
4. Emerging sector signals
5. One strategic observation for investors or founders
"""
    response = llm.invoke([HumanMessage(content=eco_prompt)])
    final = (f"🌐 **Ecosystem Intelligence**\n\n{response.content}\n\n---\n"
             f"*Source: cb_objects sector + geo rollup | SQL: {sql_ms:.1f}ms*")
    return {
        **state,
        "messages": [*state["messages"], response.__class__(content=final)],
        "sql_ms": sql_ms,
        "confidence_score": 0.81,
        "sources": ["cb_objects"],
    }

Check for:
1. HALLUCINATION: Does the response make claims not supported by data/context?
2. SQL ACCURACY: If SQL was used, is the interpretation of results correct?
3. GROUNDING: Are claims attributed to sources?
4. CONFIDENCE: Does confidence level match evidence strength?

def critic_node(state: EnterpriseState) -> EnterpriseState:
    """Validate last assistant response. Fail-open: exceptions pass through."""
    last_response = state["messages"][-1].content if state["messages"] else ""
    sql_result = state.get("sql_result","N/A") or "N/A"
    route = state.get("route","general")
    critic_input = f"""Route: {route}
Last Response (first 600 chars): {last_response[:600]}
SQL Result (if any, first 300 chars): {str(sql_result)[:300]}
"""
    try:
        resp = llm_fast.invoke([
            SystemMessage(content=CRITIC_PROMPT),
            HumanMessage(content=critic_input)
        ])
        text = re.sub(r"```json|```", "", resp.content.strip()).strip()
        verdict = json.loads(text)
        passed = verdict.get("passed", True)
        confidence = float(verdict.get("confidence", state.get("confidence_score", 0.8) or 0.8))
        issues = verdict.get("issues", [])
        if issues:
            print(f"  ⚠️  Critic flagged: {issues}")
        else:
            print(f"  ✅ Critic passed (confidence: {confidence:.2f})")
    except Exception:
        passed = True
        confidence = state.get("confidence_score", 0.8) or 0.8
    return {**state, "validator_passed": passed, "confidence_score": confidence}

def build_pipeline_chart():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT stage, COUNT(*) as deals, SUM(deal_value) as total_value
        FROM sales_pipeline GROUP BY stage
    """, conn)
    conn.close()
    fig = px.bar(df, x="stage", y="total_value", color="deals",
                 title="Sales Pipeline Value by Stage", template="plotly_dark",
                 color_continuous_scale="Teal")
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

def build_funding_chart():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT sector, SUM(amount_usd)/1e6 as total_m
        FROM startup_funding GROUP BY sector ORDER BY total_m DESC
    """, conn)
    conn.close()
    fig = px.bar(df, x="total_m", y="sector", orientation="h",
                 title="Enterprise Funding by Sector ($M)", template="plotly_dark",
                 color="total_m", color_continuous_scale="Viridis")
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

def get_all_sectors() -> list:
    try:
        conn = sqlite3.connect(CB_DB_PATH)
        df = pd.read_sql_query("""
            SELECT DISTINCT category_code FROM cb_objects
            WHERE entity_type='Company' AND category_code != 'unknown'
              AND category_code IS NOT NULL
            ORDER BY category_code LIMIT 50
        """, conn)
        conn.close()
        return df["category_code"].tolist()
    except Exception:
        return ["web","mobile","enterprise","biotech","cleantech","fintech","ai","saas"]


def run_ecosystem_query(sector, status, country):
    try:
        conn = sqlite3.connect(CB_DB_PATH)
        where = ["entity_type='Company'"]
        if sector and sector != "All":
            where.append(f"category_code='{sector}'")
        if status and status != "All":
            where.append(f"status='{status}'")
        if country and country.strip():
            where.append(f"country_code='{country.strip().upper()}'")
        where_str = " AND ".join(where)
        df = pd.read_sql_query(f"""
            SELECT category_code, status, country_code,
                   COUNT(*) as company_count,
                   ROUND(AVG(funding_total_usd)/1e6, 2) as avg_funding_m,
                   ROUND(SUM(funding_total_usd)/1e6, 2) as total_funding_m
            FROM cb_objects WHERE {where_str}
            GROUP BY category_code, status, country_code
            ORDER BY total_funding_m DESC LIMIT 50
        """, conn)
        conn.close()
        fig = px.bar(df.head(20), x="category_code", y="total_funding_m", color="status",
                     title="Total Funding by Sector & Status ($M)", template="plotly_dark",
                     labels={"total_funding_m":"Total Funding ($M)","category_code":"Sector"},
                     color_discrete_sequence=px.colors.qualitative.Vivid)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        return df, fig
    except Exception as e:
        return pd.DataFrame({"error":[str(e)]}), go.Figure()


def load_acquisition_data():
    try:
        conn = sqlite3.connect(CB_DB_PATH)
        df = pd.read_sql_query("""
            SELECT o.name, COUNT(*) as deals,
                   ROUND(SUM(a.price_amount)/1e6, 2) as total_spend_m,
                   ROUND(AVG(a.price_amount)/1e6, 2) as avg_deal_m,
                   MIN(a.acquired_at) as first_deal,
                   MAX(a.acquired_at) as latest_deal
            FROM cb_acquisitions a
            JOIN cb_objects o ON o.id = a.acquiring_object_id
            GROUP BY o.id, o.name ORDER BY deals DESC LIMIT 30
        """, conn)
        conn.close()
        clusters = pd.DataFrame(detect_acquisition_clusters())
        return df, clusters if not clusters.empty else pd.DataFrame({"message":["No anomalous acquirers detected."]})
    except Exception as e:
        return pd.DataFrame({"error":[str(e)]}), pd.DataFrame()

Funding landscape data (sector signals):
{sql_data[:500]}