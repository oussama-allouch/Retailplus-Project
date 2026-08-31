# =============================================================================
# RetailPlus — dashboard/views/p4_products.py
# Page 4 : Products & Category Performance
# =============================================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from components.header import render_header
from components.kpi_card import render_kpi
from styles import apply_plotly_theme, PALETTE, PLOTLY_COLORS
from db_connector import get_ventes_par_categorie, get_performance_produits


def render_page(selected_year: int = 2024, selected_store: str = "Tous les magasins"):
    """Rendu de la vue Products & Categories."""
    render_header(
        title="Products & Category Intelligence",
        subtitle="Analyse de la rentabilité par rayon, arborescence des sous-catégories et top références",
        active_filter_label=selected_store
    )

    df_cat = get_ventes_par_categorie()
    df_prod = get_performance_produits(limit=50)

    if df_cat.empty:
        st.warning("Aucune donnée de catégorie disponible.")
        return

    # ── 1. KPI Cards Produits ────────────────────────────────────────────────
    top_cat = df_cat.sort_values("ca_ttc", ascending=False).iloc[0]
    best_marge_cat = df_cat.sort_values("marge_pct", ascending=False).iloc[0]
    total_refs = df_cat["nb_references"].sum()
    total_ca = df_cat["ca_ttc"].sum()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi(
            title="Références Actives",
            value=f"{total_refs:,}",
            variance_text="5 Rayons principaux",
            variance_type="neutral",
            subtitle="Catalogue produit"
        )
    with c2:
        render_kpi(
            title="Rayon n°1 (Revenu)",
            value=top_cat["categorie"],
            variance_text=f"{(top_cat['ca_ttc']/total_ca*100):.1f}% du CA",
            variance_type="positive",
            subtitle=f"{top_cat['ca_ttc']/1e6:.1f}M MAD"
        )
    with c3:
        render_kpi(
            title="Rayon n°1 (Rentabilité)",
            value=best_marge_cat["categorie"],
            variance_text=f"{best_marge_cat['marge_pct']:.1f}% marge",
            variance_type="positive",
            subtitle="Meilleure marge unitaire"
        )
    with c4:
        render_kpi(
            title="Volume Global Écoulé",
            value=f"{df_cat['quantite_vendue'].sum():,}",
            variance_text="Articles vendus",
            variance_type="neutral",
            subtitle="Débit commercial"
        )

    st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

    # ── 2. Graphiques : Treemap et Matrice Marge/Volume ───────────────────────
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-header'>🏷️ Contribution au Chiffre d'Affaires par Rayon</div>", unsafe_allow_html=True)

        fig_bar = px.bar(
            df_cat,
            x="categorie",
            y="ca_ttc",
            color="marge_pct",
            text=df_cat["ca_ttc"].apply(lambda v: f"{v/1e6:.1f}M"),
            color_continuous_scale="Viridis",
            labels={"ca_ttc": "CA TTC (MAD)", "categorie": "Rayon", "marge_pct": "Taux Marge (%)"}
        )
        fig_bar = apply_plotly_theme(fig_bar, height=360)
        st.plotly_chart(fig_bar, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-header'>📦 Volume d'Articles par Catégorie</div>", unsafe_allow_html=True)

        fig_vol = px.pie(
            df_cat,
            values="quantite_vendue",
            names="categorie",
            hole=0.45,
            color_discrete_sequence=PLOTLY_COLORS
        )
        fig_vol = apply_plotly_theme(fig_vol, height=360)
        st.plotly_chart(fig_vol, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── 3. Top 20 Produits les Plus Vendus ────────────────────────────────────
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>🏆 Top 20 des Produits Générateurs de Chiffre d'Affaires</div>", unsafe_allow_html=True)

    df_top_prod = df_prod.head(20).copy()
    df_top_display = df_top_prod[[
        "produit_nom", "categorie", "sous_categorie", "fournisseur_nom",
        "prix_vente_ttc", "marge_unitaire", "total_quantite_vendue", "chiffre_affaires_ttc", "marge_brute_totale", "taux_marge_pct"
    ]].copy()

    df_top_display.columns = [
        "Produit", "Catégorie", "Sous-Catégorie", "Fournisseur",
        "Prix TTC (MAD)", "Marge Unit (MAD)", "Quantité Vendue", "CA TTC (MAD)", "Marge Totale (MAD)", "Marge (%)"
    ]

    st.dataframe(
        df_top_display.style.format({
            "Prix TTC (MAD)": "{:,.2f}",
            "Marge Unit (MAD)": "{:,.2f}",
            "Quantité Vendue": "{:,.0f}",
            "CA TTC (MAD)": "{:,.0f}",
            "Marge Totale (MAD)": "{:,.0f}",
            "Marge (%)": "{:.2f}%"
        }),
        use_container_width=True,
        height=380
    )
    st.markdown("</div>", unsafe_allow_html=True)
