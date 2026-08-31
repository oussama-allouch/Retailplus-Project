# =============================================================================
# RetailPlus — dashboard/styles.py
# Design System & Thème Enterprise BI (CSS + Plotly)
# =============================================================================

import streamlit as st
import plotly.graph_objects as go

# ─── 1. Injection CSS Globale (Enterprise Dark Theme) ─────────────────────────
ENTERPRISE_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* Global Typography & Canvas */
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: #090d16 !important;
        color: #f1f5f9 !important;
    }

    /* Streamlit Main Container Spacing */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2.5rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 1600px !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0b1120 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
    }
    
    section[data-testid="stSidebar"] .block-container {
        padding-top: 2rem !important;
        padding-left: 1.25rem !important;
        padding-right: 1.25rem !important;
    }

    /* Header Container */
    .enterprise-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: linear-gradient(180deg, #111827 0%, #0b1120 100%);
        padding: 20px 28px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.07);
        margin-bottom: 20px;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.4);
    }
    
    .header-title-group h1 {
        font-size: 22px !important;
        font-weight: 700 !important;
        color: #f8fafc !important;
        margin: 0 !important;
        letter-spacing: -0.02em;
    }
    
    .header-title-group p {
        font-size: 13px !important;
        color: #94a3b8 !important;
        margin: 4px 0 0 0 !important;
    }

    .header-meta {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    /* Metric Cards */
    .kpi-card {
        background: #0f172a;
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
        transition: transform 0.15s ease, border-color 0.15s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .kpi-card:hover {
        border-color: rgba(6, 182, 212, 0.4);
        transform: translateY(-2px);
    }

    .kpi-title {
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #94a3b8;
    }

    .kpi-main-val {
        font-size: 26px;
        font-weight: 700;
        color: #f8fafc;
        margin: 6px 0 4px 0;
        letter-spacing: -0.02em;
    }

    .kpi-footer {
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 12px;
        color: #64748b;
        margin-top: 4px;
    }

    .kpi-badge-positive {
        display: inline-flex;
        align-items: center;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 600;
        background: rgba(16, 185, 129, 0.12);
        color: #10b981;
    }

    .kpi-badge-negative {
        display: inline-flex;
        align-items: center;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 600;
        background: rgba(239, 68, 68, 0.12);
        color: #ef4444;
    }

    .kpi-badge-neutral {
        display: inline-flex;
        align-items: center;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 600;
        background: rgba(148, 163, 184, 0.12);
        color: #94a3b8;
    }

    /* Section Containers */
    .section-card {
        background: #0f172a;
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 12px;
        padding: 22px;
        margin-bottom: 20px;
    }

    .section-header {
        font-size: 15px;
        font-weight: 600;
        color: #f8fafc;
        margin-bottom: 14px;
        letter-spacing: -0.01em;
    }

    /* Business Insights Cards */
    .insight-card {
        background: #111827;
        border-left: 3px solid #06b6d4;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
        font-size: 13px;
        color: #cbd5e1;
    }
    
    .insight-card b {
        color: #f8fafc;
    }

    /* Business Alerts */
    .alert-critical {
        background: rgba(239, 68, 68, 0.08);
        border-left: 3px solid #ef4444;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
        font-size: 13px;
        color: #fca5a5;
    }

    .alert-warning {
        background: rgba(245, 158, 11, 0.08);
        border-left: 3px solid #f59e0b;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
        font-size: 13px;
        color: #fcd34d;
    }

    .alert-info {
        background: rgba(6, 182, 212, 0.08);
        border-left: 3px solid #06b6d4;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
        font-size: 13px;
        color: #a5f3fc;
    }

    /* Status Badges */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 500;
        background: rgba(6, 182, 212, 0.1);
        border: 1px solid rgba(6, 182, 212, 0.2);
        color: #22d3ee;
    }
    
    .status-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background-color: #10b981;
        box-shadow: 0 0 8px #10b981;
    }

    /* Filter Bar */
    .filter-bar {
        background: #0b1120;
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 10px;
        padding: 12px 18px;
        margin-bottom: 20px;
    }

    /* Dataframes Styling */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }
</style>
"""

def inject_styles():
    """Injecte la feuille de style globale Enterprise BI."""
    st.markdown(ENTERPRISE_CSS, unsafe_allow_html=True)


# ─── 2. Thème Plotly Épuré "retailplus_dark" ─────────────────────────────────
PALETTE = {
    "cyan":    "#06b6d4",
    "blue":    "#3b82f6",
    "violet":  "#8b5cf6",
    "emerald": "#10b981",
    "amber":   "#f59e0b",
    "rose":    "#ec4899",
    "slate":   "#64748b",
}

PLOTLY_COLORS = [
    PALETTE["cyan"],
    PALETTE["blue"],
    PALETTE["emerald"],
    PALETTE["violet"],
    PALETTE["amber"],
    PALETTE["rose"]
]


def apply_plotly_theme(fig: go.Figure, height: int = 350) -> go.Figure:
    """Applique un style professionnel épuré aux graphiques Plotly."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        margin=dict(l=16, r=16, t=36, b=16),
        font=dict(family="Inter, sans-serif", size=12, color="#94a3b8"),
        title=dict(
            font=dict(family="Inter, sans-serif", size=14, color="#f8fafc", weight=600),
            x=0.01,
            y=0.98,
            xanchor="left",
            yanchor="top"
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(255, 255, 255, 0.05)",
            zeroline=False,
            showline=True,
            linecolor="rgba(255, 255, 255, 0.1)",
            tickfont=dict(size=11, color="#64748b"),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255, 255, 255, 0.05)",
            zeroline=False,
            showline=False,
            tickfont=dict(size=11, color="#64748b"),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color="#94a3b8"),
            bgcolor="rgba(0,0,0,0)"
        ),
        hoverlabel=dict(
            bgcolor="#1e293b",
            bordercolor="rgba(255,255,255,0.1)",
            font=dict(family="Inter, sans-serif", size=12, color="#f8fafc")
        )
    )
    return fig
