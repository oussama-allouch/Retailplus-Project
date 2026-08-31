# =============================================================================
# RetailPlus — dashboard/views/p7_returns.py
# Page 7 : Returns & Quality Assurance
# =============================================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from components.header import render_header
from components.kpi_card import render_kpi
from styles import apply_plotly_theme, PALETTE, PLOTLY_COLORS
from db_connector import get_analyse_retours


def render_page(selected_year: int = 2024, selected_store: str = "Tous les magasins"):
    """Rendu de la vue Returns & Quality."""
    render_header(
        title="Returns & Quality Assurance",
        subtitle="Analyse des réclamations clients, motifs d'insatisfaction et impact financier des remboursements",
        active_filter_label=selected_store
    )

    df_ret = get_analyse_retours()

    if df_ret.empty:
        st.warning("Aucune donnée de retour disponible.")
        return

    if selected_store != "Tous les magasins":
        df_filtered = df_ret[df_ret["magasin_nom"] == selected_store]
    else:
        df_filtered = df_ret

    # ── 1. KPI Cards Retours ─────────────────────────────────────────────────
    total_retours = df_filtered["total_retours"].sum()
    total_rembourse = df_filtered["total_montant_rembourse"].sum()
    top_motif = df_filtered.groupby("motif")["total_retours"].sum().sort_values(ascending=False).index[0]
    total_qte = df_filtered["total_quantite_retournee"].sum()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi(
            title="Total Articles Retournés",
            value=f"{total_retours:,}",
            variance_text=f"{total_qte:,} unités",
            variance_type="neutral",
            subtitle="SAV et réclamations"
        )
    with c2:
        render_kpi(
            title="Montant Total Remboursé",
            value=f"{total_rembourse:,.0f} MAD",
            variance_text="Impact financier",
            variance_type="negative",
            subtitle="Avoirs et remboursements"
        )
    with c3:
        render_kpi(
            title="Motif Principal",
            value=top_motif,
            variance_text="1ère cause de retour",
            variance_type="negative",
            subtitle="Priorité contrôle qualité"
        )
    with c4:
        render_kpi(
            title="Taux Moyen de Retour",
            value="2.09%",
            variance_text="Conforme benchmark (<3%)",
            variance_type="positive",
            subtitle="Sur 3.83M transactions"
        )

    st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

    # ── 2. Graphiques : Motifs et Rayons ──────────────────────────────────────
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-header'>🔄 Répartition des Retours par Motif</div>", unsafe_allow_html=True)

        df_motif = df_filtered.groupby("motif", as_index=False)["total_retours"].sum().sort_values("total_retours", ascending=False)

        fig_motif = px.pie(
            df_motif,
            values="total_retours",
            names="motif",
            hole=0.45,
            color_discrete_sequence=PLOTLY_COLORS
        )
        fig_motif = apply_plotly_theme(fig_motif, height=340)
        st.plotly_chart(fig_motif, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-header'>💸 Montant Remboursé par Rayon (MAD)</div>", unsafe_allow_html=True)

        df_cat_ret = df_filtered.groupby("categorie_produit", as_index=False)["total_montant_rembourse"].sum().sort_values("total_montant_rembourse", ascending=False)

        fig_cat = px.bar(
            df_cat_ret,
            x="categorie_produit",
            y="total_montant_rembourse",
            text=df_cat_ret["total_montant_rembourse"].apply(lambda v: f"{v/1e6:.1f}M"),
            color="total_montant_rembourse",
            color_continuous_scale="Reds",
            labels={"total_montant_rembourse": "Montant Remboursé (MAD)", "categorie_produit": "Rayon"}
        )
        fig_cat = apply_plotly_theme(fig_cat, height=340)
        st.plotly_chart(fig_cat, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── 3. Tableau Détaillé des Retours ───────────────────────────────────────
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>📋 Récapitulatif des Retours par Magasin et Rayon</div>", unsafe_allow_html=True)

    df_ret_display = df_filtered[[
        "magasin_nom", "categorie_produit", "motif",
        "total_retours", "total_quantite_retournee", "total_montant_rembourse"
    ]].copy()

    df_ret_display.columns = [
        "Magasin", "Rayon", "Motif de Réclamation",
        "Nombre Retours", "Quantité", "Montant Remboursé (MAD)"
    ]

    st.dataframe(
        df_ret_display.style.format({
            "Nombre Retours": "{:,.0f}",
            "Quantité": "{:,.0f}",
            "Montant Remboursé (MAD)": "{:,.2f}"
        }),
        use_container_width=True,
        height=320
    )
    st.markdown("</div>", unsafe_allow_html=True)
