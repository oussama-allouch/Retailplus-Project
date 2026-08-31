# =============================================================================
# RetailPlus — dashboard/components/header.py
# Header professionnel d'entreprise avec bouton de basculement Dark / Light Mode
# =============================================================================

import streamlit as st


def render_header(title: str, subtitle: str, active_filter_label: str = None):
    """Affiche le header d'entreprise avec métadonnées et le bouton Dark/Light Mode."""

    # Initialisation du thème dans session_state (par défaut : dark)
    if "theme" not in st.session_state:
        st.session_state["theme"] = "dark"

    is_dark = st.session_state["theme"] == "dark"

    col_title, col_toggle = st.columns([4.2, 1.2])

    with col_title:
        meta_badge = f"<span class='status-badge'><span class='status-dot'></span> DWH Gold Active</span>"
        filter_badge = (
            f"<span class='status-badge' style='opacity: 0.85;'>Filtre: {active_filter_label}</span>"
            if active_filter_label
            else ""
        )

        html = f"""
        <div class="enterprise-header" style="margin-bottom: 0px;">
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

    with col_toggle:
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        btn_label = "☀️ Mode Clair" if is_dark else "🌙 Mode Sombre"
        if st.button(btn_label, key="btn_toggle_theme_header", use_container_width=True):
            st.session_state["theme"] = "light" if is_dark else "dark"
            st.rerun()

    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
