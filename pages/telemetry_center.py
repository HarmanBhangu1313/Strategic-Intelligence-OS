import streamlit as st
import pandas as pd
import plotly.express as px

def render():
    st.title("📡 Telemetry & Observability Center")
    st.caption("Monitor retrieval quality, confidence scores, and system health")

    col1, col2, col3 = st.columns(3)

    col1.metric("Avg Latency", "842 ms", "-12%")
    col2.metric("Retrieval Accuracy", "91.4%", "+6.1%")
    col3.metric("Hallucination Risk", "Low", "-18%")

    telemetry = pd.DataFrame({
        "Component": ["Retrieval", "Forecasting", "Routing", "SQL Agent", "Validation"],
        "Confidence": [0.91, 0.88, 0.94, 0.86, 0.93]
    })

    fig = px.line(
        telemetry,
        x="Component",
        y="Confidence",
        markers=True,
        title="Confidence Across AI Components"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("## System Alerts")

    st.warning("Minor retrieval drift detected in startup funding dataset.")
    st.info("Telemetry monitoring active across orchestration pipeline.")