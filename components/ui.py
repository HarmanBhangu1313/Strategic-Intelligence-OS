"""
ARIA — Reusable UI Components
"""

import streamlit as st


def page_header(title: str, subtitle: str, badge: str = "LIVE", badge_color: str = "#00ff88"):
    st.markdown(f"""
    <div class="fade-in" style="
        border-bottom: 1px solid rgba(0,200,255,0.08);
        padding-bottom: 1.2rem; margin-bottom: 1.8rem;
        display: flex; align-items: flex-end; justify-content: space-between;
    ">
        <div>
            <div style="font-family:'JetBrains Mono',monospace; font-size:0.62rem;
                        color:#3d5a7a; letter-spacing:0.18em; text-transform:uppercase;
                        margin-bottom:0.3rem;">ARIA Intelligence OS</div>
            <h1 style="font-family:'Syne',sans-serif; font-weight:800; font-size:1.9rem;
                       color:#e8f0ff; letter-spacing:-0.03em; margin:0; line-height:1.1;">
                {title}</h1>
            <p style="font-family:'JetBrains Mono',monospace; font-size:0.72rem;
                      color:#7a94b8; margin-top:0.4rem;">{subtitle}</p>
        </div>
        <div style="display:flex; align-items:center; gap:0.5rem;
                    background:rgba(0,0,0,0.3); border:1px solid rgba(0,200,255,0.12);
                    border-radius:20px; padding:0.35rem 0.9rem;">
            <div style="width:6px;height:6px;border-radius:50%;background:{badge_color};
                        box-shadow:0 0 8px {badge_color}80;"></div>
            <span style="font-family:'JetBrains Mono',monospace; font-size:0.62rem;
                         color:{badge_color}; letter-spacing:0.12em;">{badge}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def kpi_card(label: str, value: str, delta: str = "", delta_up: bool = True,
             accent: str = "#00c8ff", icon: str = ""):
    delta_class = "up" if delta_up else "down"
    delta_arrow = "▲" if delta_up else "▼"
    delta_html = f'<div class="kpi-delta {delta_class}">{delta_arrow} {delta}</div>' if delta else ""
    icon_html = f'<div style="font-size:1.2rem; margin-bottom:0.3rem;">{icon}</div>' if icon else ""

    st.markdown(f"""
    <div class="kpi-card" style="--accent-color:{accent};">
        {icon_html}
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def panel(title: str, dot_color: str = "#00c8ff"):
    """Returns a context object — use as markdown container wrapper manually."""
    st.markdown(f"""
    <div class="panel-header">
        <div class="panel-dot" style="background:{dot_color}; box-shadow:0 0 8px {dot_color}60;"></div>
        <span class="panel-title">{title}</span>
    </div>
    """, unsafe_allow_html=True)


def confidence_bar(label: str, value: int, color: str = "#00c8ff"):
    bar_color = color
    bg = f"rgba({int(color[1:3], 16)},{int(color[3:5], 16)},{int(color[5:7], 16)}, 0.15)"
    st.markdown(f"""
    <div style="margin-bottom:0.8rem;">
        <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
            <span style="font-family:'JetBrains Mono',monospace; font-size:0.7rem; color:#7a94b8;">{label}</span>
            <span style="font-family:'JetBrains Mono',monospace; font-size:0.7rem; color:{bar_color}; font-weight:600;">{value}%</span>
        </div>
        <div class="conf-bar-wrap">
            <div class="conf-bar-fill" style="width:{value}%; background:linear-gradient(90deg, {bar_color}80, {bar_color});"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def trace_log(entries: list[dict]):
    """entries: [{ts, agent, msg, status}] where status in ok/warn/err/info"""
    rows = ""
    for e in entries:
        cls = {"ok": "trace-ok", "warn": "trace-warn", "err": "trace-err"}.get(e.get("status", ""), "")
        rows += f"""
        <div class="trace-item">
            <span class="trace-ts">{e['ts']}</span>
            <span class="trace-agent">{e['agent']}</span>
            <span class="trace-msg {cls}">{e['msg']}</span>
        </div>"""
    st.markdown(f"""
    <div style="max-height:280px; overflow-y:auto; background:var(--bg-elevated);
                border-radius:8px; padding:0.6rem; border:1px solid var(--border-subtle);">
        {rows}
    </div>
    """, unsafe_allow_html=True)


def section_divider(label: str = ""):
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:1rem; margin:1.5rem 0;">
        <div style="flex:1; height:1px; background:rgba(0,200,255,0.08);"></div>
        {f'<span style="font-family:JetBrains Mono,monospace; font-size:0.6rem; color:#3d5a7a; letter-spacing:0.15em;">{label}</span>' if label else ''}
        <div style="flex:1; height:1px; background:rgba(0,200,255,0.08);"></div>
    </div>
    """, unsafe_allow_html=True)