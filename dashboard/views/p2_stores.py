# =============================================================================
# RetailPlus — dashboard/views/p2_stores.py
# Page 2 : Store Performance & Regional Analytics
# =============================================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from components.header import render_header
from components.kpi_card import render_kpi
from styles import apply_plotly_theme, PALETTE
from db_connector import get_performance_magasins


def render_page(selected_year: int = 2024, selected_store: str = "Tous les magasins"):
    """Rendu de la vue Store Performance."""
    render_header(
        title="Store Performance & Regional Analytics",
        subtitle="Benchmark comparatif des 5 magasins physiques au Maroc (Casablanca, Rabat, Marrakech, Fès, Tanger)",
        active_filter_label=selected_store
    )

    df_mag = get_performance_magasins()
    if df_mag.empty:
        st.warning("Aucune donnée de magasin disponible.")
        return

    # Si un magasin spécifique est sélectionné, on peut mettre en valeur ses métriques
    if selected_store != "Tous les magasins":
        df_filtered = df_mag[df_mag["magasin_nom"] == selected_store]
    else:
        df_filtered = df_mag

    # ── 1. KPI Cards Magasins ────────────────────────────────────────────────
    top_store = df_mag.sort_values("chiffre_affaires_ttc", ascending=False).iloc[0]
    avg_ca_m2 = df_mag["ca_par_m2"].mean()
    best_marge_store = df_mag.sort_values("taux_marge_pct", ascending=False).iloc[0]
    best_ret_store = df_mag.sort_values("taux_retour_pct", ascending=True).iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi(
            title="Magasin Leader (CA)",
            value=top_store["magasin_nom"].replace("RetailPlus ", ""),
            variance_text=f"{top_store['chiffre_affaires_ttc']/1e6:.1f}M MAD",
            variance_type="positive",
            subtitle="1er au classement national"
        )
    with c2:
        render_kpi(
            title="Rendement Moyen au m²",
            value=f"{avg_ca_m2:,.0f} MAD/m²",
            variance_text="Surface moy: 4 440 m²",
            variance_type="neutral",
            subtitle="Efficacité commerciale"
        )
    with c3:
        render_kpi(
            title="Meilleur Taux de Marge",
            value=f"{best_marge_store['taux_marge_pct']:.2f}%",
            variance_text=best_marge_store["magasin_nom"].replace("RetailPlus ", ""),
            variance_type="positive",
            subtitle="Rentabilité opérationnelle"
        )
    with c4:
        render_kpi(
            title="Plus Faible Taux de Retour",
            value=f"{best_ret_store['taux_retour_pct']:.2f}%",
            variance_text=best_ret_store["magasin_nom"].replace("RetailPlus ", ""),
            variance_type="positive",
            subtitle="Satisfaction client maximale"
        )

    st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

    # ── 2. Graphiques Comparatifs ─────────────────────────────────────────────
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-header'>📊 Comparatif Chiffre d'Affaires vs Marge Brute (MAD)</div>", unsafe_allow_html=True)

        fig_compare = go.Figure()
        fig_compare.add_trace(go.Bar(
            x=df_mag["magasin_nom"].str.replace("RetailPlus ", ""),
            y=df_mag["chiffre_affaires_ttc"],
            name="CA TTC",
            marker_color=PALETTE["cyan"],
            hovertemplate="<b>%{x}</b><br>CA TTC: %{y:,.0f} MAD<extra></extra>"
        ))
        fig_compare.add_trace(go.Bar(
            x=df_mag["magasin_nom"].str.replace("RetailPlus ", ""),
            y=df_mag["marge_brute_totale"],
            name="Marge Brute",
            marker_color=PALETTE["violet"],
            hovertemplate="<b>%{x}</b><br>Marge: %{y:,.0f} MAD<extra></extra>"
        ))
        fig_compare.update_layout(barmode="group")
        fig_compare = apply_plotly_theme(fig_compare, height=360)
        st.plotly_chart(fig_compare, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-header'>🎯 Panier Moyen vs Taux de Retour (%)</div>", unsafe_allow_html=True)

        fig_scatter = px.scatter(
            df_mag,
            x="panier_moyen_ttc",
            y="taux_retour_pct",
            size="surface_m2",
            color="ville",
            text=df_mag["magasin_nom"].str.replace("RetailPlus ", ""),
            labels={"panier_moyen_ttc": "Panier Moyen (MAD)", "taux_retour_pct": "Taux de Retour (%)"}
        )
        fig_scatter.update_traces(textposition="top center")
        fig_scatter = apply_plotly_theme(fig_scatter, height=360)
        st.plotly_chart(fig_scatter, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── 3. Tableau de Synthèse Complet des Magasins ───────────────────────────
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>📋 Tableau de Performance Détaillé par Magasin</div>", unsafe_allow_html=True)

    df_display = df_mag[[
        "magasin_nom", "ville", "region", "surface_m2",
        "total_transactions", "chiffre_affaires_ttc", "marge_brute_totale",
        "taux_marge_pct", "panier_moyen_ttc", "ca_par_m2", "taux_retour_pct"
    ]].copy()

    df_display.columns = [
        "Magasin", "Ville", "Région", "Surface (m²)",
        "Transactions", "CA TTC (MAD)", "Marge Brute (MAD)",
        "Taux Marge (%)", "Panier Moyen (MAD)", "CA / m² (MAD)", "Taux Retour (%)"
    ]

    st.dataframe(
        df_display.style.format({
            "Surface (m²)": "{:,.0f}",
            "Transactions": "{:,.0f}",
            "CA TTC (MAD)": "{:,.0f}",
            "Marge Brute (MAD)": "{:,.0f}",
            "Taux Marge (%)": "{:.2f}%",
            "Panier Moyen (MAD)": "{:.2f}",
            "CA / m² (MAD)": "{:,.0f}",
            "Taux Retour (%)": "{:.2f}%"
        }),
        use_container_width=True,
        height=220
    )
    st.markdown("</div>", unsafe_allow_html=True)
