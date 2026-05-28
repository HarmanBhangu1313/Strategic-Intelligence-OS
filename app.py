"""
Strategic Intelligence OS
Enterprise AI Command Center
"""

import streamlit as st

# ─────────────────────────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Strategic Intelligence OS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# Global Theme
# ─────────────────────────────────────────────────────────────

from components.theme import inject_global_css
inject_global_css()

# ─────────────────────────────────────────────────────────────
# Sidebar Navigation
# ─────────────────────────────────────────────────────────────

from components.sidebar import render_sidebar
render_sidebar()

# ─────────────────────────────────────────────────────────────
# Page Router
# ─────────────────────────────────────────────────────────────

from pages.executive_dashboard import render as executive_render
from pages.orchestration_center import render as orchestration_render
from pages.intelligence_report import render as intelligence_render
from pages.telemetry_center import render as telemetry_render

page = st.session_state.get("page", "executive")

if page == "executive":
    executive_render()

elif page == "orchestration":
    orchestration_render()

elif page == "intelligence_report":
    intelligence_render()

elif page == "telemetry":
    telemetry_render()

else:
    st.error("Page not found.")
