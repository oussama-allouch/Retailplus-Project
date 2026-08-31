# =============================================================================
# RetailPlus — dashboard/views/p3_sales.py
# Page 3 : Sales Analytics & Trend Decomposition
# =============================================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from components.header import render_header
from components.kpi_card import render_kpi
from styles import apply_plotly_theme, PALETTE
from db_connector import get_ventes_mensuelles, get_kpis_globaux


def render_page(selected_year: int = 2024, selected_store: str = "Tous les magasins"):
    """Rendu de la vue Sales Analytics."""
    render_header(
        title="Sales Analytics & Revenue Breakdown",
        subtitle="Décomposition chronologique, analyse fiscale (HT / TVA / TTC) et tendances saisonnières",
        active_filter_label=f"{selected_store} • {selected_year}" if selected_year else selected_store
    )

    df_kpi = get_kpis_globaux(year=selected_year, store=selected_store)
    df_mensuel = get_ventes_mensuelles(year=selected_year, store=selected_store)

    if df_kpi.empty:
        st.warning("Aucune donnée de vente disponible.")
        return

    kpi = df_kpi.iloc[0]
    montant_tva = kpi['chiffre_affaires_ttc'] - kpi['chiffre_affaires_ht']

    # ── 1. KPI Cards Financières ─────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi(
            title="Chiffre d'Affaires HT",
            value=f"{kpi['chiffre_affaires_ht']:,.0f} MAD",
            variance_text="Base imposable",
            variance_type="neutral",
            subtitle="Montant net HT"
        )
    with c2:
        render_kpi(
            title="TVA Collectée (20%)",
            value=f"{montant_tva:,.0f} MAD",
            variance_text=f"{(montant_tva/kpi['chiffre_affaires_ttc']*100):.1f}% du TTC",
            variance_type="neutral",
            subtitle="Contribution fiscale"
        )
    with c3:
        render_kpi(
            title="Chiffre d'Affaires TTC",
            value=f"{kpi['chiffre_affaires_ttc']:,.0f} MAD",
            variance_text="Total encaissé",
            variance_type="positive",
            subtitle="Montant client final"
        )
    with c4:
        render_kpi(
            title="Total Articles Écoulés",
            value=f"{kpi['total_articles_vendus']:,}",
            variance_text=f"{kpi['total_transactions']:,} transactions",
            variance_type="positive",
            subtitle="Volume physique"
        )

    st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

    # ── 2. Décomposition Trimestrielle & Analyse Mensuelle ───────────────────
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-header'>📊 Chiffre d'Affaires par Trimestre (MAD)</div>", unsafe_allow_html=True)

        df_quarter = df_mensuel.groupby("trimestre", as_index=False).agg({
            "chiffre_affaires_ttc": "sum",
            "marge_brute_totale": "sum",
            "total_transactions": "sum"
        }).sort_values("trimestre")

        df_quarter["Trimestre_Label"] = "T" + df_quarter["trimestre"].astype(str)

        fig_q = go.Figure()
        fig_q.add_trace(go.Bar(
            x=df_quarter["Trimestre_Label"],
            y=df_quarter["chiffre_affaires_ttc"],
            name="CA TTC",
            marker_color=PALETTE["cyan"],
            text=df_quarter["chiffre_affaires_ttc"].apply(lambda v: f"{v/1e6:.1f}M"),
            textposition="auto"
        ))
        fig_q = apply_plotly_theme(fig_q, height=340)
        st.plotly_chart(fig_q, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-header'>📅 Tendance du Panier Moyen Mensuel (MAD)</div>", unsafe_allow_html=True)

        df_pm = df_mensuel.groupby(["mois_num", "mois_nom"], as_index=False).agg({
            "chiffre_affaires_ttc": "sum",
            "total_transactions": "sum"
        }).sort_values("mois_num")
        df_pm["panier_moyen"] = df_pm["chiffre_affaires_ttc"] / df_pm["total_transactions"]

        fig_pm = px.line(
            df_pm,
            x="mois_nom",
            y="panier_moyen",
            markers=True,
            line_shape="spline",
            color_discrete_sequence=[PALETTE["emerald"]]
        )
        fig_pm = apply_plotly_theme(fig_pm, height=340)
        fig_pm.update_layout(xaxis_title="", yaxis_title="Panier Moyen (MAD)")
        st.plotly_chart(fig_pm, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── 3. Tableau Récapitulatif Mensuel ─────────────────────────────────────
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>📋 Synthèse Mensuelle Consolidée</div>", unsafe_allow_html=True)

    df_table = df_mensuel.groupby(["annee", "mois_num", "mois_nom"], as_index=False).agg({
        "total_transactions": "sum",
        "articles_vendus": "sum",
        "chiffre_affaires_ht": "sum",
        "chiffre_affaires_ttc": "sum",
        "marge_brute_totale": "sum"
    }).sort_values(["annee", "mois_num"])

    df_table["taux_marge"] = (df_table["marge_brute_totale"] / df_table["chiffre_affaires_ht"]) * 100
    df_table["panier_moyen"] = df_table["chiffre_affaires_ttc"] / df_table["total_transactions"]

    df_table_display = df_table[[
        "mois_nom", "total_transactions", "articles_vendus",
        "chiffre_affaires_ht", "chiffre_affaires_ttc", "marge_brute_totale", "taux_marge", "panier_moyen"
    ]].copy()

    df_table_display.columns = [
        "Mois", "Transactions", "Articles Vendus",
        "CA HT (MAD)", "CA TTC (MAD)", "Marge Brute (MAD)", "Marge (%)", "Panier Moyen (MAD)"
    ]

    st.dataframe(
        df_table_display.style.format({
            "Transactions": "{:,.0f}",
            "Articles Vendus": "{:,.0f}",
            "CA HT (MAD)": "{:,.0f}",
            "CA TTC (MAD)": "{:,.0f}",
            "Marge Brute (MAD)": "{:,.0f}",
            "Marge (%)": "{:.2f}%",
            "Panier Moyen (MAD)": "{:.2f}"
        }),
        use_container_width=True,
        height=320
    )
    st.markdown("</div>", unsafe_allow_html=True)
