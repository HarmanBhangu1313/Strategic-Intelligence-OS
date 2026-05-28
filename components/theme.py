"""
ARIA Global CSS Theme — Stable Streamlit Version
"""

import streamlit as st


def inject_global_css():

    st.markdown("""
    <style>

    :root {
        --bg-void: #020408;
        --bg-surface: #080d14;
        --bg-card: #0f1a26;

        --accent-cyan: #00c8ff;
        --accent-green: #00ff88;
        --accent-violet: #8855ff;
        --accent-amber: #ffaa00;

        --text-primary: #e8f0ff;
        --text-secondary: #7a94b8;
        --text-muted: #3d5a7a;
    }

    html, body, [data-testid="stAppViewContainer"] {
        background: var(--bg-void) !important;
        color: var(--text-primary) !important;
        font-family: sans-serif !important;
    }

    [data-testid="stSidebar"] {
        background: var(--bg-surface) !important;
        border-right: 1px solid rgba(0,200,255,0.08);
    }

    .main .block-container {
        padding-top: 1.2rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }

    h1, h2, h3 {
        color: var(--text-primary) !important;
        font-weight: 700 !important;
    }

    .stButton > button {
        background: rgba(0,200,255,0.08) !important;
        border: 1px solid rgba(0,200,255,0.18) !important;
        color: var(--accent-cyan) !important;
        border-radius: 8px !important;
    }

    .stButton > button:hover {
        background: rgba(0,200,255,0.14) !important;
    }

    [data-testid="metric-container"] {
        background: var(--bg-card) !important;
        border: 1px solid rgba(0,200,255,0.08);
        border-radius: 10px;
        padding: 1rem;
    }

    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
    }

    </style>
    """, unsafe_allow_html=True)
