"""
Strategic Intelligence OS — Executive Dashboard
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import time

from components.ui import (
    page_header,
    kpi_card,
    confidence_bar,
    panel,
    section_divider
)


def render():

    page_header(
        "Executive Intelligence Dashboard",
        "Real-time market analysis · Competitive intelligence · Strategic opportunity scoring",
        badge="LIVE INTEL",
    )

    # ─────────────────────────────────────────────────────────────
    # Query Input
    # ─────────────────────────────────────────────────────────────

    st.markdown("## Strategic Intelligence Query")

    col_q, col_btn = st.columns([5, 1])

    with col_q:
        query = st.text_input(
            "",
            value="Analyze AI/ML startup funding trends and identify top acquisition targets in 2024",
            label_visibility="collapsed"
        )

    with col_btn:
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        run = st.button("⬡ ANALYZE", use_container_width=True)

    # ─────────────────────────────────────────────────────────────
    # Multi-Agent Execution Simulation
    # ─────────────────────────────────────────────────────────────

    if run:

        st.markdown("## ⚙️ Multi-Agent Execution Pipeline")

        with st.spinner("Planner Agent → Building execution strategy..."):
            time.sleep(1)

        st.success("Planner Agent Complete")

        with st.spinner("Retrieval Agent → Searching enterprise intelligence databases..."):
            time.sleep(1)

        st.success("Retrieval Agent Complete")

        with st.spinner("SQL Agent → Running structured market intelligence queries..."):
            time.sleep(1)

        st.success("SQL Agent Complete")

        with st.spinner("Analyst Agent → Performing strategic trend analysis..."):
            time.sleep(1)

        st.success("Analyst Agent Complete")

        with st.spinner("Critic Agent → Validating evidence quality..."):
            time.sleep(1)

        st.warning("Critic detected weak retrieval evidence")

        with st.spinner("Self-Correction Loop → Rewriting query and retrying retrieval..."):
            time.sleep(1)

        st.success("Confidence improved from 61% → 94%")

        st.markdown("---")

        st.markdown("## 🧠 Strategic Intelligence Report")

        st.markdown(f"""
        ### Query
        `{query}`

        ### Executive Summary

        The Strategic Intelligence OS identified strong investment momentum
        across enterprise AI infrastructure and autonomous workflow tooling.

        Key strategic signals detected:
        - Accelerated venture funding in AI observability platforms
        - Increased acquisition activity around telemetry-driven systems
        - Enterprise demand shifting toward autonomous orchestration tooling
        - Strong investor concentration in infrastructure-layer AI startups

        ### AI-Generated Recommendations
        - Prioritize enterprise AI infrastructure monitoring
        - Track observability platform consolidation opportunities
        - Monitor autonomous AI workflow adoption trends
        - Expand telemetry coverage for strategic forecasting

        ### Final Confidence Score
        `94.2%`
        """)

    # ─────────────────────────────────────────────────────────────
    # KPI Cards
    # ─────────────────────────────────────────────────────────────

    section_divider("KEY PERFORMANCE INDICATORS")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        kpi_card(
            "Funding Analyzed",
            "$706M",
            "+34% YoY",
            True,
            "#00c8ff",
            "💰"
        )

    with c2:
        kpi_card(
            "Companies Tracked",
            "15",
            "+3 this week",
            True,
            "#00ff88",
            "⬡"
        )

    with c3:
        kpi_card(
            "Confidence Score",
            "94.2%",
            "+2.1%",
            True,
            "#8855ff",
            "◉"
        )

    with c4:
        kpi_card(
            "Queries Processed",
            "2,847",
            "+127 today",
            True,
            "#ffaa00",
            "▲"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────
    # Confidence Breakdown
    # ─────────────────────────────────────────────────────────────

    panel("Agent Confidence Breakdown")

    confidence_bar("Retrieval Quality", 92, "#00c8ff")
    confidence_bar("Analysis Depth", 88, "#8855ff")
    confidence_bar("Source Reliability", 95, "#00ff88")
    confidence_bar("Hallucination Shield", 97, "#ffaa00")

    st.markdown("<br>", unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────
    # Market Intelligence Chart
    # ─────────────────────────────────────────────────────────────

    st.markdown("## 📈 Sector Funding Velocity")

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    values = [2.1, 2.8, 3.6, 4.8, 6.1, 8.2]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=months,
            y=values,
            mode="lines+markers",
            line=dict(color="#00c8ff", width=3),
            fill="tozeroy"
        )
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=350,
        margin=dict(l=20, r=20, t=40, b=20),
    )

    st.plotly_chart(fig, use_container_width=True)
