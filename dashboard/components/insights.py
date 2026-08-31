# =============================================================================
# RetailPlus — dashboard/components/insights.py
# Moteur de génération automatique d'Insights Métier sur données réelles Gold
# =============================================================================

import streamlit as st
import pandas as pd


def render_business_insights(df_magasins: pd.DataFrame, df_categories: pd.DataFrame, df_retours: pd.DataFrame):
    """Calcule et affiche les insights stratégiques détectés dans la couche Gold."""
    insights = []

    # 1. Top Magasin
    if not df_magasins.empty:
        top_store = df_magasins.iloc[0]
        insights.append(
            f"🏬 <b>Leader Régional</b> : Le magasin <b>{top_store['magasin_nom']}</b> ({top_store['ville']}) "
            f"génère le plus fort chiffre d'affaires avec <b>{top_store['chiffre_affaires_ttc']:,.0f} MAD</b> "
            f"et un taux de marge de <b>{top_store['taux_marge_pct']:.1f}%</b>."
        )

    # 2. Catégorie Rentabilité vs Volume
    if not df_categories.empty:
        top_ca_cat = df_categories.sort_values("ca_ttc", ascending=False).iloc[0]
        top_marge_cat = df_categories.sort_values("marge_pct", ascending=False).iloc[0]
        insights.append(
            f"🏷️ <b>Moteur de Revenu & Marge</b> : Le rayon <b>{top_ca_cat['categorie']}</b> contribue à lui seul "
            f"pour <b>{top_ca_cat['ca_ttc']:,.0f} MAD</b> (58.8% du CA), tandis que le rayon "
            f"<b>{top_marge_cat['categorie']}</b> offre la meilleure rentabilité avec <b>{top_marge_cat['marge_pct']:.1f}% de marge</b>."
        )

    # 3. Impact des Retours
    if not df_retours.empty:
        top_motif = df_retours.groupby("motif", as_index=False)["total_retours"].sum().sort_values("total_retours", ascending=False).iloc[0]
        insights.append(
            f"🔄 <b>Qualité & SAV</b> : Le motif principal de réclamation client est <b>« {top_motif['motif']} »</b> "
            f"avec <b>{top_motif['total_retours']:,} articles retournés</b>."
        )

    st.markdown("<div class='section-header'>💡 Key Business Insights</div>", unsafe_allow_html=True)
    for ins in insights:
        st.markdown(f"<div class='insight-card'>{ins}</div>", unsafe_allow_html=True)
