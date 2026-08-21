# =============================================================================
# RetailPlus — dashboard/app.py
# Application Dashboard Décisionnel BI — Modern Data Platform
# =============================================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from db_connector import (
    get_kpis_globaux,
    get_ventes_mensuelles,
    get_performance_magasins,
    get_performance_produits,
    get_ventes_par_categorie,
    get_segmentation_clients,
    get_top_clients,
    get_gestion_stocks,
    get_analyse_retours
)

# ─── Configuration de la page ────────────────────────────────────────────────
st.set_page_config(
    page_title="RetailPlus — Data Platform BI Dashboard",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Thème Custom & Styles CSS ───────────────────────────────────────────────
st.markdown("""
<style>
    /* Global Styling */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Header Container */
    .header-box {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 24px 32px;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        margin-bottom: 24px;
    }
    
    .header-title {
        font-size: 28px;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    
    .header-subtitle {
        color: #94a3b8;
        font-size: 14px;
        margin-top: 4px;
    }

    /* Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #111827 100%);
        padding: 20px;
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 0.06);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(56, 189, 248, 0.4);
    }
    
    .metric-label {
        color: #94a3b8;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-value {
        color: #f8fafc;
        font-size: 26px;
        font-weight: 800;
        margin-top: 6px;
    }
    
    .metric-sub {
        color: #10b981;
        font-size: 12px;
        font-weight: 600;
        margin-top: 4px;
    }
    
    /* Tag / Pill */
    .pill {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 600;
        background: rgba(56, 189, 248, 0.15);
        color: #38bdf8;
    }
</style>
""", unsafe_allow_html=True)

# ─── Barre Latérale (Sidebar) ─────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shopping-cart-loaded.png", width=64)
    st.markdown("## **RetailPlus BI**")
    st.markdown("<div class='pill'>Architecture Médaillon (Gold)</div>", unsafe_allow_html=True)
    st.markdown("---")
    
    menu = st.radio(
        "Navigation Analytique",
        [
            "📊 Vue d'Ensemble Exécutive",
            "🏬 Performance Magasins & Villes",
            "🏷️ Analyse Produits & Catégories",
            "👥 Segmentation Clients & Fidélité",
            "📦 Stocks & Logistique",
            "🔄 Analyse des Retours & Qualité",
        ],
        index=0
    )
    
    st.markdown("---")
    st.markdown("### 🔍 Filtres Globaux")
    df_magasins = get_performance_magasins()
    liste_magasins = ["Tous les magasins"] + list(df_magasins["magasin_nom"].unique())
    magasin_selected = st.selectbox("Magasin", liste_magasins)
    
    st.markdown("---")
    st.markdown(
        "<div style='color: #64748b; font-size: 11px;'>"
        "Data Warehouse: <b>PostgreSQL 15 (Gold)</b><br>"
        "Transactions analysées: <b>3.83M</b><br>"
        "Plateforme: <b>Spark & Airflow</b>"
        "</div>",
        unsafe_allow_html=True
    )

# ─── En-tête Principal ───────────────────────────────────────────────────────
st.markdown("""
<div class="header-box">
    <h1 class="header-title">🛒 RetailPlus — Tableau de Bord Décisionnel</h1>
    <div class="header-subtitle">Plateforme d'Intelligence d'Affaires & Suivi des Performances Commerciales (Maroc)</div>
</div>
""", unsafe_allow_html=True)


# =============================================================================
# 1. VUE D'ENSEMBLE EXÉCUTIVE
# =============================================================================
if menu == "📊 Vue d'Ensemble Exécutive":
    st.markdown("### 📈 Indicateurs Clés de Performance (KPIs Globaux)")
    
    df_kpi = get_kpis_globaux()
    if not df_kpi.empty:
        kpi = df_kpi.iloc[0]
        
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Chiffre d'Affaires TTC</div>
                <div class="metric-value">{kpi['chiffre_affaires_ttc']:,.0f} MAD</div>
                <div class="metric-sub">▲ HT: {kpi['chiffre_affaires_ht']:,.0f} MAD</div>
            </div>
            """, unsafe_allow_html=True)
            
        with c2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Marge Brute Totale</div>
                <div class="metric-value">{kpi['marge_brute_totale']:,.0f} MAD</div>
                <div class="metric-sub">Taux de marge: {kpi['taux_marge_pct']:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
            
        with c3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total Transactions</div>
                <div class="metric-value">{kpi['total_transactions']:,}</div>
                <div class="metric-sub">Tickets de caisse validés</div>
            </div>
            """, unsafe_allow_html=True)
            
        with c4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Panier Moyen TTC</div>
                <div class="metric-value">{kpi['panier_moyen_ttc']:.2f} MAD</div>
                <div class="metric-sub">Articles: {kpi['total_articles_vendus']:,}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with c5:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Base Clients Actifs</div>
                <div class="metric-value">{kpi['clients_actifs']:,}</div>
                <div class="metric-sub">5 Magasins physiques</div>
            </div>
            """, unsafe_allow_html=True)
            
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Graphiques d'évolution mensuelle
    col_g1, col_g2 = st.columns([3, 2])
    
    df_mensuel = get_ventes_mensuelles()
    
    with col_g1:
        st.markdown("#### 📅 Évolution du Chiffre d'Affaires Mensuel (MAD)")
        if magasin_selected != "Tous les magasins":
            df_filtered = df_mensuel[df_mensuel["magasin_nom"] == magasin_selected]
        else:
            df_filtered = df_mensuel
            
        df_chart = df_filtered.groupby(["annee", "mois_num", "mois_nom"], as_index=False).agg({
            "chiffre_affaires_ttc": "sum",
            "marge_brute_totale": "sum",
            "total_transactions": "sum"
        }).sort_values(["annee", "mois_num"])
        
        df_chart["Periode"] = df_chart["mois_nom"] + " " + df_chart["annee"].astype(str)
        
        fig_trend = px.line(
            df_chart,
            x="Periode",
            y="chiffre_affaires_ttc",
            markers=True,
            line_shape="spline",
            title="Chiffre d'Affaires TTC Mensuel",
            color_discrete_sequence=["#38bdf8"]
        )
        fig_trend.add_bar(
            x=df_chart["Periode"],
            y=df_chart["marge_brute_totale"],
            name="Marge Brute",
            marker_color="rgba(129, 140, 248, 0.4)"
        )
        fig_trend.update_layout(
            template="plotly_dark",
            xaxis_title="Mois",
            yaxis_title="Montant (MAD)",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_trend, use_container_width=True)
        
    with col_g2:
        st.markdown("#### 🏬 Répartition du CA par Magasin")
        df_mag = get_performance_magasins()
        fig_pie = px.pie(
            df_mag,
            values="chiffre_affaires_ttc",
            names="magasin_nom",
            hole=0.45,
            color_discrete_sequence=px.colors.sequential.Tealgrn
        )
        fig_pie.update_layout(template="plotly_dark", showlegend=True)
        st.plotly_chart(fig_pie, use_container_width=True)


# =============================================================================
# 2. PERFORMANCE MAGASINS & VILLES
# =============================================================================
elif menu == "🏬 Performance Magasins & Villes":
    st.markdown("### 🏬 Performance Comparée des 5 Magasins au Maroc")
    
    df_mag = get_performance_magasins()
    
    col1, col2 = st.columns([3, 2])
    with col1:
        fig_bar = px.bar(
            df_mag,
            x="magasin_nom",
            y="chiffre_affaires_ttc",
            color="taux_marge_pct",
            text_auto=".2s",
            title="Chiffre d'Affaires et Taux de Marge (%)",
            labels={"chiffre_affaires_ttc": "CA TTC (MAD)", "magasin_nom": "Magasin", "taux_marge_pct": "Marge %"},
            color_continuous_scale="Blues"
        )
        fig_bar.update_layout(template="plotly_dark")
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with col2:
        fig_scatter = px.scatter(
            df_mag,
            x="panier_moyen_ttc",
            y="taux_retour_pct",
            size="total_transactions",
            color="ville",
            text="magasin_nom",
            title="Panier Moyen vs Taux de Retour (%)",
            labels={"panier_moyen_ttc": "Panier Moyen (MAD)", "taux_retour_pct": "Taux de Retour (%)"}
        )
        fig_scatter.update_layout(template="plotly_dark")
        st.plotly_chart(fig_scatter, use_container_width=True)
        
    st.markdown("#### 📋 Tableau de Synthèse des Magasins")
    st.dataframe(
        df_mag[[
            "magasin_nom", "ville", "region", "surface_m2", 
            "total_transactions", "chiffre_affaires_ttc", "marge_brute_totale", 
            "taux_marge_pct", "panier_moyen_ttc", "ca_par_m2", "taux_retour_pct"
        ]].rename(columns={
            "magasin_nom": "Magasin", "ville": "Ville", "region": "Région",
            "surface_m2": "Surface (m²)", "total_transactions": "Transactions",
            "chiffre_affaires_ttc": "CA TTC (MAD)", "marge_brute_totale": "Marge Brute (MAD)",
            "taux_marge_pct": "Marge (%)", "panier_moyen_ttc": "Panier Moyen (MAD)",
            "ca_par_m2": "CA / m² (MAD)", "taux_retour_pct": "Taux Retour (%)"
        }),
        use_container_width=True
    )


# =============================================================================
# 3. ANALYSE PRODUITS & CATÉGORIES
# =============================================================================
elif menu == "🏷️ Analyse Produits & Catégories":
    st.markdown("### 🏷️ Ventes & Rentabilité par Rayon et Produit")
    
    df_cat = get_ventes_par_categorie()
    
    c1, c2 = st.columns([1, 1])
    with c1:
        fig_cat = px.bar(
            df_cat,
            x="categorie",
            y="ca_ttc",
            color="marge_pct",
            title="Chiffre d'Affaires par Catégorie de Produit (MAD)",
            labels={"ca_ttc": "CA TTC (MAD)", "categorie": "Catégorie", "marge_pct": "Marge %"},
            color_continuous_scale="Viridis"
        )
        fig_cat.update_layout(template="plotly_dark")
        st.plotly_chart(fig_cat, use_container_width=True)
        
    with c2:
        fig_vol = px.pie(
            df_cat,
            values="quantite_vendue",
            names="categorie",
            title="Volume d'Articles Vendus par Catégorie",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        fig_vol.update_layout(template="plotly_dark")
        st.plotly_chart(fig_vol, use_container_width=True)
        
    st.markdown("#### 🏆 Top 20 des Produits les Plus Rentables")
    df_prod = get_performance_produits(20)
    
    fig_top = px.bar(
        df_prod,
        x="chiffre_affaires_ttc",
        y="produit_nom",
        orientation="h",
        color="categorie",
        title="Top 20 Produits par Chiffre d'Affaires TTC",
        labels={"chiffre_affaires_ttc": "CA TTC (MAD)", "produit_nom": "Produit"}
    )
    fig_top.update_layout(template="plotly_dark", yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_top, use_container_width=True)


# =============================================================================
# 4. SEGMENTATION CLIENTS & FIDÉLITÉ
# =============================================================================
elif menu == "👥 Segmentation Clients & Fidélité":
    st.markdown("### 👥 Analyse de la Clientèle & Segments RFM")
    
    df_seg = get_segmentation_clients()
    
    c1, c2 = st.columns([1, 1])
    with c1:
        fig_seg_pie = px.pie(
            df_seg,
            values="ca_total_ttc",
            names="segment",
            title="Contribution au Chiffre d'Affaires par Segment Client",
            hole=0.45,
            color_discrete_sequence=px.colors.sequential.Purp
        )
        fig_seg_pie.update_layout(template="plotly_dark")
        st.plotly_chart(fig_seg_pie, use_container_width=True)
        
    with c2:
        fig_seg_bar = px.bar(
            df_seg,
            x="segment",
            y="panier_moyen_segment",
            color="nb_clients",
            text_auto=True,
            title="Panier Moyen par Segment (MAD)",
            labels={"panier_moyen_segment": "Panier Moyen (MAD)", "segment": "Segment", "nb_clients": "Nb Clients"}
        )
        fig_seg_bar.update_layout(template="plotly_dark")
        st.plotly_chart(fig_seg_bar, use_container_width=True)
        
    st.markdown("#### 🌟 Top 20 Clients VIP (Plus Fortes Dépenses)")
    df_top_c = get_top_clients(20)
    st.dataframe(
        df_top_c[[
            "nom", "prenom", "client_ville", "segment", 
            "nb_achats", "total_articles_achetes", "depense_totale_ttc", 
            "panier_moyen", "marge_totale_generee"
        ]].rename(columns={
            "nom": "Nom", "prenom": "Prénom", "client_ville": "Ville", "segment": "Segment",
            "nb_achats": "Nombre Achats", "total_articles_achetes": "Articles", 
            "depense_totale_ttc": "Dépense Totale (MAD)", "panier_moyen": "Panier Moyen (MAD)",
            "marge_totale_generee": "Marge Générée (MAD)"
        }),
        use_container_width=True
    )


# =============================================================================
# 5. GESTION DES STOCKS & LOGISTIQUE
# =============================================================================
elif menu == "📦 Stocks & Logistique":
    st.markdown("### 📦 Suivi des Stocks, Ruptures & Approvisionnements")
    
    df_stock = get_gestion_stocks()
    
    c1, c2 = st.columns([1, 1])
    with c1:
        df_rupt = df_stock.groupby("categorie", as_index=False).agg({
            "nb_occurrences_rupture": "sum",
            "valeur_stock_moyenne_ht": "sum"
        }).sort_values("nb_occurrences_rupture", ascending=False)
        
        fig_rupt = px.bar(
            df_rupt,
            x="categorie",
            y="nb_occurrences_rupture",
            color="valeur_stock_moyenne_ht",
            title="Nombre d'Alertes de Rupture par Catégorie",
            labels={"nb_occurrences_rupture": "Alertes Rupture", "valeur_stock_moyenne_ht": "Valeur Stock (MAD)"},
            color_continuous_scale="Reds"
        )
        fig_rupt.update_layout(template="plotly_dark")
        st.plotly_chart(fig_rupt, use_container_width=True)
        
    with c2:
        df_fourn = df_stock.groupby("fournisseur_nom", as_index=False).agg({
            "delai_livraison_jours": "mean",
            "valeur_stock_moyenne_ht": "sum"
        }).sort_values("delai_livraison_jours")
        
        fig_fourn = px.bar(
            df_fourn,
            x="fournisseur_nom",
            y="delai_livraison_jours",
            title="Délai Moyen de Livraison par Fournisseur (Jours)",
            labels={"delai_livraison_jours": "Délai (Jours)", "fournisseur_nom": "Fournisseur"},
            color_discrete_sequence=["#f59e0b"]
        )
        fig_fourn.update_layout(template="plotly_dark")
        st.plotly_chart(fig_fourn, use_container_width=True)


# =============================================================================
# 6. ANALYSE DES RETOURS & QUALITÉ
# =============================================================================
elif menu == "🔄 Analyse des Retours & Qualité":
    st.markdown("### 🔄 Analyse des Retours d'Articles & Motifs de Réclamation")
    
    df_ret = get_analyse_retours()
    
    c1, c2 = st.columns([1, 1])
    with c1:
        df_motif = df_ret.groupby("motif", as_index=False).agg({
            "total_retours": "sum",
            "total_montant_rembourse": "sum"
        }).sort_values("total_retours", ascending=False)
        
        fig_motif = px.pie(
            df_motif,
            values="total_retours",
            names="motif",
            title="Répartition des Retours par Motif de Réclamation",
            hole=0.45,
            color_discrete_sequence=px.colors.sequential.Sunset
        )
        fig_motif.update_layout(template="plotly_dark")
        st.plotly_chart(fig_motif, use_container_width=True)
        
    with c2:
        df_ret_cat = df_ret.groupby("categorie_produit", as_index=False).agg({
            "total_montant_rembourse": "sum",
            "total_retours": "sum"
        }).sort_values("total_montant_rembourse", ascending=False)
        
        fig_ret_cat = px.bar(
            df_ret_cat,
            x="categorie_produit",
            y="total_montant_rembourse",
            title="Montant Total Remboursé par Rayon (MAD)",
            labels={"total_montant_rembourse": "Montant Remboursé (MAD)", "categorie_produit": "Rayon"},
            color_discrete_sequence=["#ef4444"]
        )
        fig_ret_cat.update_layout(template="plotly_dark")
        st.plotly_chart(fig_ret_cat, use_container_width=True)
