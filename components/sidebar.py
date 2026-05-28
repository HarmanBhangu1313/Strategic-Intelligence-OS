import streamlit as st


def render_sidebar():

    with st.sidebar:

        st.markdown("# ARIA")
        st.caption("Strategic Intelligence OS")

        st.divider()

        nav_items = {
            "executive": "📊 Executive Dashboard",
            "orchestration": "⚙️ Agent Orchestration",
            "intelligence_report": "🧠 Intelligence Report",
            "telemetry": "📡 Telemetry Center"
        }

        if "page" not in st.session_state:
            st.session_state.page = "executive"

        selected = st.radio(
            "Navigation",
            options=list(nav_items.keys()),
            format_func=lambda x: nav_items[x],
            index=list(nav_items.keys()).index(
                st.session_state.page
            )
        )

        st.session_state.page = selected

        st.divider()

        st.markdown("### System Status")

        col1, col2 = st.columns(2)

        col1.metric("Agents", "7/7")
        col2.metric("Uptime", "99.8%")

        col1.metric("Latency", "1.8s")
        col2.metric("Confidence", "94.2%")

        st.success("LLM: Groq • LLaMA-70B")