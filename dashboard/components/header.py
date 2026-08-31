# =============================================================================
# RetailPlus — dashboard/components/header.py
# Header professionnel pour les pages analytiques
# =============================================================================

import streamlit as st


def render_header(title: str, subtitle: str, active_filter_label: str = None):
    """Affiche le header d'entreprise avec métadonnées et statut."""
    meta_badge = f"<span class='status-badge'><span class='status-dot'></span> DWH Gold Active</span>"
    filter_badge = f"<span class='status-badge' style='background: rgba(255,255,255,0.05); border-color: rgba(255,255,255,0.1); color: #94a3b8;'>Filtre: {active_filter_label}</span>" if active_filter_label else ""
    
    html = f"""
    <div class="enterprise-header">
        <div class="header-title-group">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        <div class="header-meta">
            {filter_badge}
            {meta_badge}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
