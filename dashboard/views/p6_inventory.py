# =============================================================================
# RetailPlus — dashboard/views/p6_inventory.py
# Page 6 : Inventory & Supply Chain Performance
# =============================================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from components.header import render_header
from components.kpi_card import render_kpi
from styles import apply_plotly_theme, PALETTE
from db_connector import get_gestion_stocks


def render_page(selected_year: int = 2024, selected_store: str = "Tous les magasins"):
    """Rendu de la vue Inventory & Supply Chain."""
    render_header(
        title="Inventory & Supply Chain Intelligence",
        subtitle="Suivi des stocks immobilisés, évaluation des délais fournisseurs et prévention des ruptures",
        active_filter_label=selected_store
    )

    df_stock = get_gestion_stocks()

    if df_stock.empty:
        st.warning("Aucune donnée de stock disponible.")
        return

    if selected_store != "Tous les magasins":
        df_filtered = df_stock[df_stock["magasin_nom"] == selected_store]
    else:
        df_filtered = df_stock

    # ── 1. KPI Cards Supply Chain ────────────────────────────────────────────
    total_val_stock = df_filtered["valeur_stock_moyenne_ht"].sum()
    nb_fourn = df_stock["fournisseur_nom"].nunique()
    delai_moyen = df_stock["delai_livraison_jours"].mean()
    total_ruptures = df_filtered["nb_occurrences_rupture"].sum()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi(
            title="Valeur Stock Immobilisé",
            value=f"{total_val_stock:,.0f} MAD",
            variance_text="Moyenne HT",
            variance_type="neutral",
            subtitle="Actif circulant"
        )
    with c2:
        render_kpi(
            title="Fournisseurs Partenaires",
            value=f"{nb_fourn}",
            variance_text="Réseau d'approvisionnement",
            variance_type="positive",
            subtitle="Fournisseurs référencés"
        )
    with c3:
        render_kpi(
            title="Délai de Livraison Moyen",
            value=f"{delai_moyen:.1f} Jours",
            variance_text="Max: 14j (Samsung)",
            variance_type="neutral",
            subtitle="Lead time global"
        )
    with c4:
        render_kpi(
            title="Occurrences de Rupture",
            value=f"{total_ruptures:,}",
            variance_text="Taux de service: 99.8%",
            variance_type="positive",
            subtitle="Disponibilité rayon"
        )

    st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

    # ── 2. Graphiques : Stocks et Délais Fournisseurs ─────────────────────────
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-header'>📦 Valeur Moyenne du Stock par Rayon (MAD)</div>", unsafe_allow_html=True)

        df_cat_stock = df_filtered.groupby("categorie", as_index=False)["valeur_stock_moyenne_ht"].sum().sort_values("valeur_stock_moyenne_ht", ascending=False)

        fig_stock_cat = px.bar(
            df_cat_stock,
            x="categorie",
            y="valeur_stock_moyenne_ht",
            text=df_cat_stock["valeur_stock_moyenne_ht"].apply(lambda v: f"{v/1e3:.0f}k"),
            color="valeur_stock_moyenne_ht",
            color_continuous_scale="Teal",
            labels={"valeur_stock_moyenne_ht": "Valeur Stock (MAD)", "categorie": "Rayon"}
        )
        fig_stock_cat = apply_plotly_theme(fig_stock_cat, height=340)
        st.plotly_chart(fig_stock_cat, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-header'>🚚 Délais Moyens de Livraison par Fournisseur (Jours)</div>", unsafe_allow_html=True)

        df_fourn = df_stock.groupby("fournisseur_nom", as_index=False)["delai_livraison_jours"].mean().sort_values("delai_livraison_jours", ascending=True)

        fig_fourn = px.bar(
            df_fourn,
            x="delai_livraison_jours",
            y="fournisseur_nom",
            orientation="h",
            text="delai_livraison_jours",
            color="delai_livraison_jours",
            color_continuous_scale="Viridis",
            labels={"delai_livraison_jours": "Délai (Jours)", "fournisseur_nom": "Fournisseur"}
        )
        fig_fourn.update_traces(texttemplate="%{text:.0f} jours", textposition="outside", cliponaxis=False)
        fig_fourn = apply_plotly_theme(fig_fourn, height=340)
        fig_fourn.update_layout(yaxis_title="", xaxis_title="Délai Moyen (Jours)")
        st.plotly_chart(fig_fourn, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── 3. Synthèse Approvisionnement ─────────────────────────────────────────
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>📋 Surveillance des Stocks par Produit & Magasin</div>", unsafe_allow_html=True)

    df_stock_display = df_filtered[[
        "produit_nom", "categorie", "magasin_nom", "fournisseur_nom",
        "stock_moyen", "valeur_stock_moyenne_ht", "delai_livraison_jours", "nb_occurrences_rupture"
    ]].head(25).copy()

    df_stock_display.columns = [
        "Produit", "Catégorie", "Magasin", "Fournisseur",
        "Stock Moyen (Unités)", "Valeur Stock (MAD)", "Délai (Jours)", "Ruptures"
    ]

    st.dataframe(
        df_stock_display.style.format({
            "Stock Moyen (Unités)": "{:,.0f}",
            "Valeur Stock (MAD)": "{:,.2f}",
            "Délai (Jours)": "{:.0f}",
            "Ruptures": "{:,.0f}"
        }),
        use_container_width=True,
        height=320
    )
    st.markdown("</div>", unsafe_allow_html=True)
