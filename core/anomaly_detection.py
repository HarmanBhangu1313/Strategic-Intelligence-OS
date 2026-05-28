"""
Auto-extracted from ARIA_Strategic_Intelligence_OS.ipynb
"""

    """Anomaly detection in operational metrics: Z-score method flags values beyond 2.5 standard
    deviations. IQR method robust to non-Gaussian distributions. For time-series, seasonal
    decomposition before z-scoring reduces false positives significantly.""",


def anomaly_node(state: EnterpriseState) -> EnterpriseState:
    """Detect anomalies in operational metrics AND Crunchbase funding/acquisition data."""
    query = state["messages"][-1].content

    anomaly_prompt = f"""You are an SRE and financial analyst detecting anomalies across two systems.

print("✅ Extended anomaly detection agent ready.")