# =============================================================================
# RetailPlus — dashboard/styles.py
# Design System & Thème Enterprise BI (CSS Dual Theme + Plotly)
# =============================================================================

import streamlit as st
import plotly.graph_objects as go

# ─── 1. Thème Sombre (Enterprise Dark Theme) ──────────────────────────────────
DARK_THEME_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"], .stApp,
    .stApp > header,
    .main .block-container,
    div[data-testid="stAppViewContainer"],
    div[data-testid="stHeader"],
    div[data-testid="stToolbar"],
    div[data-testid="stDecoration"],
    div[data-testid="stStatusWidget"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: #090d16 !important;
        color: #f1f5f9 !important;
    }

    h1, h2, h3, h4, h5, h6,
    p, span, label, div,
    .stMarkdown, .stText,
    [data-testid="stMarkdownContainer"],
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] span,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3 {
        color: #f1f5f9 !important;
    }

    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span {
        background-color: #0b1120 !important;
        color: #f1f5f9 !important;
    }

    [data-testid="stRadio"] label,
    [data-testid="stRadio"] label span,
    [data-testid="stRadio"] label p,
    [data-testid="stSelectbox"] label,
    [data-testid="stSelectbox"] label span,
    div[data-baseweb="select"] {
        color: #f1f5f9 !important;
    }

    div[data-baseweb="select"] > div {
        background-color: #1e293b !important;
        border-color: rgba(255, 255, 255, 0.1) !important;
        color: #f1f5f9 !important;
    }

    div[data-baseweb="popover"] > div,
    div[data-baseweb="menu"],
    ul[role="listbox"],
    ul[role="listbox"] li {
        background-color: #1e293b !important;
        color: #f1f5f9 !important;
    }

    ul[role="listbox"] li:hover {
        background-color: #334155 !important;
    }

    .stButton > button {
        background-color: #1e293b !important;
        color: #f1f5f9 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }

    .stButton > button:hover {
        background-color: #334155 !important;
        border-color: rgba(6, 182, 212, 0.4) !important;
    }

    hr {
        border-color: rgba(255, 255, 255, 0.06) !important;
    }

    .stDataFrame, .stTable,
    [data-testid="stDataFrame"],
    [data-testid="stDataFrame"] div {
        background-color: #0f172a !important;
        color: #f1f5f9 !important;
    }

    .stAlert {
        background-color: #1e293b !important;
        color: #f1f5f9 !important;
    }

    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2.5rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 1600px !important;
    }

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

    .stPlotlyChart {
        background-color: transparent !important;
    }
</style>
"""

# ─── 2. Thème Clair (Enterprise Light Theme) ──────────────────────────────────
LIGHT_THEME_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"], .stApp,
    .stApp > header,
    .main .block-container,
    div[data-testid="stAppViewContainer"],
    div[data-testid="stHeader"],
    div[data-testid="stToolbar"],
    div[data-testid="stDecoration"],
    div[data-testid="stStatusWidget"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: #f8fafc !important;
        color: #0f172a !important;
    }

    h1, h2, h3, h4, h5, h6,
    p, span, label, div,
    .stMarkdown, .stText,
    [data-testid="stMarkdownContainer"],
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] span,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3 {
        color: #0f172a !important;
    }

    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span {
        background-color: #f1f5f9 !important;
        color: #0f172a !important;
    }

    [data-testid="stRadio"] label,
    [data-testid="stRadio"] label span,
    [data-testid="stRadio"] label p,
    [data-testid="stSelectbox"] label,
    [data-testid="stSelectbox"] label span,
    div[data-baseweb="select"] {
        color: #0f172a !important;
    }

    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border-color: #cbd5e1 !important;
        color: #0f172a !important;
    }

    div[data-baseweb="popover"] > div,
    div[data-baseweb="menu"],
    ul[role="listbox"],
    ul[role="listbox"] li {
        background-color: #ffffff !important;
        color: #0f172a !important;
    }

    ul[role="listbox"] li:hover {
        background-color: #e2e8f0 !important;
    }

    .stButton > button {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1px solid #cbd5e1 !important;
    }

    .stButton > button:hover {
        background-color: #f1f5f9 !important;
        border-color: #0891b2 !important;
    }

    hr {
        border-color: #e2e8f0 !important;
    }

    .stDataFrame, .stTable,
    [data-testid="stDataFrame"],
    [data-testid="stDataFrame"] div {
        background-color: #ffffff !important;
        color: #0f172a !important;
    }

    .stAlert {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1px solid #e2e8f0 !important;
    }

    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2.5rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 1600px !important;
    }

    .enterprise-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
        padding: 20px 28px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        margin-bottom: 20px;
        box-shadow: 0 2px 10px -2px rgba(0, 0, 0, 0.05);
    }
    
    .header-title-group h1 {
        font-size: 22px !important;
        font-weight: 700 !important;
        color: #0f172a !important;
        margin: 0 !important;
        letter-spacing: -0.02em;
    }
    
    .header-title-group p {
        font-size: 13px !important;
        color: #64748b !important;
        margin: 4px 0 0 0 !important;
    }

    .header-meta {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .kpi-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        transition: transform 0.15s ease, border-color 0.15s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .kpi-card:hover {
        border-color: #0891b2;
        transform: translateY(-2px);
    }

    .kpi-title {
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #64748b;
    }

    .kpi-main-val {
        font-size: 26px;
        font-weight: 700;
        color: #0f172a;
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
        color: #059669;
    }

    .kpi-badge-negative {
        display: inline-flex;
        align-items: center;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 600;
        background: rgba(239, 68, 68, 0.12);
        color: #dc2626;
    }

    .kpi-badge-neutral {
        display: inline-flex;
        align-items: center;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 600;
        background: rgba(100, 116, 139, 0.12);
        color: #475569;
    }

    .section-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 22px;
        margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
    }

    .section-header {
        font-size: 15px;
        font-weight: 600;
        color: #0f172a;
        margin-bottom: 14px;
        letter-spacing: -0.01em;
    }

    .insight-card {
        background: #f8fafc;
        border-left: 3px solid #0891b2;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
        font-size: 13px;
        color: #334155;
    }
    
    .insight-card b {
        color: #0f172a;
    }

    .alert-critical {
        background: rgba(239, 68, 68, 0.08);
        border-left: 3px solid #dc2626;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
        font-size: 13px;
        color: #991b1b;
    }

    .alert-warning {
        background: rgba(245, 158, 11, 0.08);
        border-left: 3px solid #d97706;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
        font-size: 13px;
        color: #92400e;
    }

    .alert-info {
        background: rgba(6, 182, 212, 0.08);
        border-left: 3px solid #0891b2;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
        font-size: 13px;
        color: #155e75;
    }

    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 500;
        background: rgba(6, 182, 212, 0.08);
        border: 1px solid rgba(6, 182, 212, 0.3);
        color: #0891b2;
    }
    
    .status-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background-color: #10b981;
        box-shadow: 0 0 8px #10b981;
    }

    .stPlotlyChart {
        background-color: transparent !important;
    }
</style>
"""


def inject_styles(is_dark: bool = True, *args, **kwargs):
    """Injecte la feuille de style globale dynamique (Dark ou Light)."""
    if "is_dark" in kwargs:
        is_dark = kwargs["is_dark"]
    css = DARK_THEME_CSS if is_dark else LIGHT_THEME_CSS
    st.markdown(css, unsafe_allow_html=True)


# ─── 3. Thèmes Plotly Dynamiques ─────────────────────────────────────────────
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


def apply_plotly_theme(fig: go.Figure, is_dark: bool = None, height: int = 350) -> go.Figure:
    """Applique un style Plotly adapté au thème actif (Dark ou Light)."""
    if is_dark is None:
        is_dark = st.session_state.get("theme", "dark") == "dark"

    template = "plotly_dark" if is_dark else "plotly_white"
    text_color = "#94a3b8" if is_dark else "#475569"
    title_color = "#f8fafc" if is_dark else "#0f172a"
    grid_color = "rgba(255, 255, 255, 0.05)" if is_dark else "rgba(0, 0, 0, 0.06)"
    line_color = "rgba(255, 255, 255, 0.1)" if is_dark else "rgba(0, 0, 0, 0.1)"
    hover_bg = "#1e293b" if is_dark else "#ffffff"
    hover_txt = "#f8fafc" if is_dark else "#0f172a"

    fig.update_layout(
        template=template,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        margin=dict(l=16, r=16, t=36, b=16),
        font=dict(family="Inter, sans-serif", size=12, color=text_color),
        title=dict(
            font=dict(family="Inter, sans-serif", size=14, color=title_color, weight=600),
            x=0.01,
            y=0.98,
            xanchor="left",
            yanchor="top"
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor=grid_color,
            zeroline=False,
            showline=True,
            linecolor=line_color,
            tickfont=dict(size=11, color=text_color),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=grid_color,
            zeroline=False,
            showline=False,
            tickfont=dict(size=11, color=text_color),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color=text_color),
            bgcolor="rgba(0,0,0,0)"
        ),
        hoverlabel=dict(
            bgcolor=hover_bg,
            bordercolor="rgba(0,0,0,0.1)",
            font=dict(family="Inter, sans-serif", size=12, color=hover_txt)
        )
    )
    return fig
