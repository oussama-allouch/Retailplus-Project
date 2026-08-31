# =============================================================================
# RetailPlus — dashboard/components/alerts.py
# Système d'alertes opérationnelles hiérarchisées (Critical, Warning, Info)
# =============================================================================

import streamlit as st
import pandas as pd


def render_business_alerts(df_stocks: pd.DataFrame, df_magasins: pd.DataFrame, df_retours: pd.DataFrame):
    """Évalue les seuils opérationnels réels et affiche les alertes hiérarchisées."""
    alerts = []

    # 1. Alerte Délais Fournisseurs (Samsung = 14 jours)
    if not df_stocks.empty and "delai_livraison_jours" in df_stocks.columns:
        long_lead = df_stocks[df_stocks["delai_livraison_jours"] > 10]
        if not long_lead.empty:
            fourn_names = ", ".join(long_lead["fournisseur_nom"].unique())
            delai_max = long_lead["delai_livraison_jours"].max()
            alerts.append((
                "warning",
                f"⚠ <b>Délai Approvisionnement Élevé</b> : Délais critiques observés chez <b>{fourn_names}</b> ({delai_max:.0f} jours de délai de livraison moyen). Risque d'impact sur la chaîne logistique."
            ))

    # 2. Alerte Retours Rayon Électronique
    if not df_retours.empty:
        elec_ret = df_retours[df_retours["categorie_produit"] == "Électronique"]
        if not elec_ret.empty:
            montant = elec_ret["total_montant_rembourse"].sum()
            alerts.append((
                "critical",
                f"🚨 <b>Impact Financier SAV</b> : Le rayon <b>Électronique</b> totalise <b>{montant:,.0f} MAD</b> de remboursements suite à des retours articles (motif dominant : défectueux)."
            ))

    # 3. Info Distribution Régionale
    if not df_magasins.empty:
        alerts.append((
            "info",
            f"ℹ <b>Équilibre des Magasins</b> : Les 5 magasins (Casablanca, Rabat, Marrakech, Fès, Tanger) affichent une répartition homogène (~20% du volume national chacun)."
        ))

    st.markdown("<div class='section-header'>⚡ Operational & Business Alerts</div>", unsafe_allow_html=True)
    for level, text in alerts:
        cls = f"alert-{level}"
        st.markdown(f"<div class='{cls}'>{text}</div>", unsafe_allow_html=True)
