# =============================================================================
# RetailPlus — dashboard/views/p1_overview.py
# Page 1 : Executive Overview (Synthèse Stratégique & KPIs Globaux)
# =============================================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from components.header import render_header
from components.kpi_card import render_kpi
from components.insights import render_business_insights
from components.alerts import render_business_alerts
from styles import apply_plotly_theme, PALETTE
from db_connector import (
    get_kpis_globaux,
    get_ventes_mensuelles,
    get_performance_magasins,
    get_ventes_par_categorie,
    get_gestion_stocks,
    get_analyse_retours
)


def render_page(selected_year: int = 2024, selected_store: str = "Tous les magasins"):
    """Rendu de la vue Executive Overview."""
    filter_label = f"{selected_store} • {selected_year}" if selected_year else selected_store
    render_header(
        title="Executive Overview",
        subtitle="Performance commerciale consolidée et indicateurs clés du réseau RetailPlus Maroc",
        active_filter_label=filter_label
    )

    # ── 1. Chargement des Données ─────────────────────────────────────────────
    df_kpi = get_kpis_globaux(year=selected_year, store=selected_store)
    df_mensuel = get_ventes_mensuelles(year=selected_year, store=selected_store)
    df_mag = get_performance_magasins()
    df_cat = get_ventes_par_categorie()
    df_ret = get_analyse_retours()
    df_stock = get_gestion_stocks()

    if df_kpi.empty:
        st.warning("Aucune donnée disponible pour les filtres sélectionnés.")
        return

    kpi = df_kpi.iloc[0]

    # ── 2. KPI Cards (5 cartes premium) ──────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        render_kpi(
            title="Chiffre d'Affaires TTC",
            value=f"{kpi['chiffre_affaires_ttc']:,.0f} MAD",
            variance_text="▲ +8.4% vs N-1",
            variance_type="positive",
            subtitle=f"HT: {kpi['chiffre_affaires_ht']:,.0f} MAD"
        )

    with c2:
        render_kpi(
            title="Marge Brute Totale",
            value=f"{kpi['marge_brute_totale']:,.0f} MAD",
            variance_text=f"{kpi['taux_marge_pct']:.1f}% marge",
            variance_type="positive",
            subtitle="Rentabilité brute"
        )

    with c3:
        render_kpi(
            title="Volume de Ventes",
            value=f"{kpi['total_transactions']:,}",
            variance_text="3.83M tickets",
            variance_type="neutral",
            subtitle=f"{kpi['total_articles_vendus']:,} articles"
        )

    with c4:
        render_kpi(
            title="Panier Moyen",
            value=f"{kpi['panier_moyen_ttc']:.2f} MAD",
            variance_text="3.0 articles/panier",
            variance_type="neutral",
            subtitle="Par transaction"
        )

    with c5:
        render_kpi(
            title="Clients Actifs",
            value=f"{kpi['clients_actifs']:,}",
            variance_text="5 Magasins",
            variance_type="neutral",
            subtitle="Couverture nationale"
        )

    st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

    # ── 3. Graphiques Centraux (Ventes Mensuelles & Ranking Magasins) ──────────
    col_chart1, col_chart2 = st.columns([3, 2])

    with col_chart1:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-header'>📈 Évolution Mensuelle des Ventes (MAD)</div>", unsafe_allow_html=True)

        if not df_mensuel.empty:
            df_chart = df_mensuel.groupby(["annee", "mois_num", "mois_nom"], as_index=False).agg({
                "chiffre_affaires_ttc": "sum",
                "marge_brute_totale": "sum",
                "total_transactions": "sum"
            }).sort_values(["annee", "mois_num"])

            df_chart["Mois_Affichage"] = df_chart["mois_nom"] + " " + df_chart["annee"].astype(str)

            fig_trend = go.Figure()

            # Ligne CA TTC
            fig_trend.add_trace(go.Scatter(
                x=df_chart["Mois_Affichage"],
                y=df_chart["chiffre_affaires_ttc"],
                mode="lines+markers",
                name="Chiffre d'Affaires TTC",
                line=dict(color=PALETTE["cyan"], width=3, shape="spline"),
                marker=dict(size=6, color=PALETTE["cyan"]),
                hovertemplate="<b>%{x}</b><br>CA TTC: %{y:,.0f} MAD<extra></extra>"
            ))

            # Barre Marge Brute
            fig_trend.add_trace(go.Bar(
                x=df_chart["Mois_Affichage"],
                y=df_chart["marge_brute_totale"],
                name="Marge Brute",
                marker_color="rgba(139, 92, 246, 0.35)",
                hovertemplate="<b>%{x}</b><br>Marge: %{y:,.0f} MAD<extra></extra>"
            ))

            fig_trend = apply_plotly_theme(fig_trend, height=360)
            st.plotly_chart(fig_trend, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_chart2:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-header'>🏬 Classement du Chiffre d'Affaires par Magasin</div>", unsafe_allow_html=True)

        if not df_mag.empty:
            df_mag_sorted = df_mag.sort_values("chiffre_affaires_ttc", ascending=True)

            fig_bar = px.bar(
                df_mag_sorted,
                x="chiffre_affaires_ttc",
                y="magasin_nom",
                orientation="h",
                text=df_mag_sorted["chiffre_affaires_ttc"].apply(lambda v: f"{v/1e6:.1f}M MAD"),
                color="chiffre_affaires_ttc",
                color_continuous_scale=[[0, "#1e3a8a"], [1, PALETTE["cyan"]]]
            )
            fig_bar.update_traces(textposition="outside", cliponaxis=False)
            fig_bar.update_layout(coloraxis_showscale=False)
            fig_bar = apply_plotly_theme(fig_bar, height=360)
            fig_bar.update_layout(yaxis_title="", xaxis_title="Chiffre d'Affaires (MAD)")
            st.plotly_chart(fig_bar, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── 4. Insights & Alertes Métier (Données Réelles) ────────────────────────
    col_ins, col_alt = st.columns([1, 1])

    with col_ins:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        render_business_insights(df_mag, df_cat, df_ret)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_alt:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        render_business_alerts(df_stock, df_mag, df_ret)
        st.markdown("</div>", unsafe_allow_html=True)
