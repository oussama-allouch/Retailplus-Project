# =============================================================================
# RetailPlus — dashboard/components/kpi_card.py
# Rendu des cartes KPI professionnelles
# =============================================================================

import streamlit as st


def render_kpi(title: str, value: str, variance_text: str = None, variance_type: str = "neutral", subtitle: str = None):
    """
    variance_type: 'positive', 'negative', 'neutral'
    """
    badge_html = ""
    if variance_text:
        badge_class = f"kpi-badge-{variance_type}"
        badge_html = f"<span class='{badge_class}'>{variance_text}</span>"
        
    sub_html = f"<span>{subtitle}</span>" if subtitle else "<span></span>"
    
    card_html = f"""
    <div class="kpi-card">
        <div class="kpi-title">{title}</div>
        <div class="kpi-main-val">{value}</div>
        <div class="kpi-footer">
            {sub_html}
            {badge_html}
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)
