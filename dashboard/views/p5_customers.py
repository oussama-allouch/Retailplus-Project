# =============================================================================
# RetailPlus — dashboard/views/p5_customers.py
# Page 5 : Customers & Loyalty Intelligence
# =============================================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from components.header import render_header
from components.kpi_card import render_kpi
from styles import apply_plotly_theme, PALETTE, PLOTLY_COLORS
from db_connector import get_segmentation_clients, get_clients_par_ville, get_top_clients


def render_page(selected_year: int = 2024, selected_store: str = "Tous les magasins"):
    """Rendu de la vue Customers & Loyalty."""
    render_header(
        title="Customers & Loyalty Intelligence",
        subtitle="Segmentation RFM, fidélité client, panier moyen et répartition géographique",
        active_filter_label=selected_store
    )

    df_seg = get_segmentation_clients()
    df_villes = get_clients_par_ville()
    df_top_clients = get_top_clients(limit=20)

    if df_seg.empty:
        st.warning("Aucune donnée client disponible.")
        return

    # ── 1. KPI Cards Clients ─────────────────────────────────────────────────
    total_clients = df_seg["nb_clients"].sum()
    top_seg = df_seg.sort_values("ca_total_ttc", ascending=False).iloc[0]
    total_ca = df_seg["ca_total_ttc"].sum()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi(
            title="Base Clients Active",
            value=f"{total_clients:,}",
            variance_text="100% avec historique",
            variance_type="positive",
            subtitle="Portefeuille client"
        )
    with c2:
        render_kpi(
            title="Segment Principal (CA)",
            value=top_seg["segment"],
            variance_text=f"{(top_seg['ca_total_ttc']/total_ca*100):.1f}% du CA",
            variance_type="positive",
            subtitle=f"{top_seg['ca_total_ttc']/1e6:.1f}M MAD"
        )
    with c3:
        render_kpi(
            title="Panier Moyen Global",
            value=f"{df_seg['panier_moyen_segment'].mean():.2f} MAD",
            variance_text="Par transaction",
            variance_type="neutral",
            subtitle="Valeur moyenne d'achat"
        )
    with c4:
        render_kpi(
            title="Achats Moyens / Client",
            value=f"{(df_seg['total_achats'].sum()/total_clients):.0f}",
            variance_text="Tickets / client",
            variance_type="neutral",
            subtitle="Fréquence d'achat"
        )

    st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

    # ── 2. Graphiques : Segments et Villes ────────────────────────────────────
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-header'>👥 Répartition du Chiffre d'Affaires par Segment</div>", unsafe_allow_html=True)

        fig_seg = px.pie(
            df_seg,
            values="ca_total_ttc",
            names="segment",
            hole=0.45,
            color_discrete_sequence=[PALETTE["cyan"], PALETTE["violet"], PALETTE["amber"]]
        )
        fig_seg = apply_plotly_theme(fig_seg, height=340)
        st.plotly_chart(fig_seg, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-header'>📍 Répartition Géographique des Clients par Ville</div>", unsafe_allow_html=True)

        fig_ville = px.bar(
            df_villes,
            x="ville",
            y="ca_total_ttc",
            color="nb_clients",
            text=df_villes["ca_total_ttc"].apply(lambda v: f"{v/1e6:.1f}M"),
            color_continuous_scale="Blues",
            labels={"ca_total_ttc": "CA TTC (MAD)", "ville": "Ville", "nb_clients": "Nombre de Clients"}
        )
        fig_ville = apply_plotly_theme(fig_ville, height=340)
        st.plotly_chart(fig_ville, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── 3. Top 20 Clients VIP ────────────────────────────────────────────────
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>🌟 Top 20 Clients VIP (Plus Fortes Contributions)</div>", unsafe_allow_html=True)

    df_top_display = df_top_clients[[
        "nom", "prenom", "client_ville", "segment",
        "nb_achats", "total_articles_achetes", "depense_totale_ttc", "panier_moyen", "marge_totale_generee"
    ]].copy()

    df_top_display.columns = [
        "Nom", "Prénom", "Ville", "Segment",
        "Nb Achats", "Articles Achetés", "Dépense Totale (MAD)", "Panier Moyen (MAD)", "Marge Générée (MAD)"
    ]

    st.dataframe(
        df_top_display.style.format({
            "Nb Achats": "{:,.0f}",
            "Articles Achetés": "{:,.0f}",
            "Dépense Totale (MAD)": "{:,.0f}",
            "Panier Moyen (MAD)": "{:.2f}",
            "Marge Générée (MAD)": "{:,.0f}"
        }),
        use_container_width=True,
        height=380
    )
    st.markdown("</div>", unsafe_allow_html=True)
