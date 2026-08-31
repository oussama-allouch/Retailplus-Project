# =============================================================================
# RetailPlus — dashboard/app.py
# Application Dashboard Décisionnel BI — Enterprise Data Analytics Platform
# =============================================================================

import streamlit as st
import sys
import os

# Ajout du répertoire courant au PYTHONPATH pour les imports relatifs
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from styles import inject_styles
from db_connector import get_performance_magasins, get_annees_disponibles

# Import des 7 vues analytiques
from views import (
    p1_overview,
    p2_stores,
    p3_sales,
    p4_products,
    p5_customers,
    p6_inventory,
    p7_returns
)

# ─── Configuration de la Page Streamlit ──────────────────────────────────────
st.set_page_config(
    page_title="RetailPlus — Enterprise BI Platform",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Injection du Design System
inject_styles()


# ─── Barre Latérale (Enterprise Navigation & Global Filters) ─────────────────
with st.sidebar:
    # Header de Marque
    st.markdown("""
    <div style="padding: 4px 0 16px 0;">
        <div style="font-size: 20px; font-weight: 800; color: #f8fafc; letter-spacing: -0.02em;">
            🛒 RetailPlus
        </div>
        <div style="font-size: 12px; font-weight: 500; color: #94a3b8; margin-top: 2px;">
            Enterprise Analytics Platform
        </div>
        <div style="margin-top: 8px;">
            <span class="status-badge" style="background: rgba(6, 182, 212, 0.12); color: #22d3ee; font-size: 10px; font-weight: 600;">
                ● GOLD DATA LAYER
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr style='border-color: rgba(255,255,255,0.06); margin: 8px 0 16px 0;'>", unsafe_allow_html=True)

    # Menu de Navigation (7 Pages)
    menu_options = [
        "Overview",
        "Store Performance",
        "Sales Analytics",
        "Products & Categories",
        "Customers & Loyalty",
        "Inventory & Supply Chain",
        "Returns & Quality"
    ]

    selected_view = st.radio(
        "Navigation",
        menu_options,
        index=0,
        label_visibility="collapsed"
    )

    st.markdown("<hr style='border-color: rgba(255,255,255,0.06); margin: 16px 0;'>", unsafe_allow_html=True)

    # ── Filtres Globaux ───────────────────────────────────────────────────────
    st.markdown("<div style='font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: #64748b; margin-bottom: 8px;'>Filtres Globaux</div>", unsafe_allow_html=True)

    # Filtre Année / Période
    annees = get_annees_disponibles()
    options_annee = ["2024 (Année Complète - Batch)", "2026 (Événements Temps Réel)", "Toutes les périodes"]
    annee_choice = st.selectbox("Période", options_annee, index=0)

    if "2024" in annee_choice:
        selected_year = 2024
    elif "2026" in annee_choice:
        selected_year = 2026
    else:
        selected_year = None

    # Filtre Magasin
    df_magasins = get_performance_magasins()
    liste_magasins = ["Tous les magasins"] + list(df_magasins["magasin_nom"].unique()) if not df_magasins.empty else ["Tous les magasins"]
    selected_store = st.selectbox("Magasin", liste_magasins, index=0)

    # Bouton Réinitialiser Filtres
    if st.button("Réinitialiser les filtres", use_container_width=True):
        st.rerun()

    # Footer Technique
    st.markdown("<hr style='border-color: rgba(255,255,255,0.06); margin: 24px 0 12px 0;'>", unsafe_allow_html=True)
    st.markdown("""
    <div style="color: #64748b; font-size: 11px; line-height: 1.6;">
        <div style="font-weight: 600; color: #94a3b8; margin-bottom: 2px;">Data Platform Architecture</div>
        PostgreSQL 15 • Spark 3.5<br>
        Airflow 2.7 • Kafka 7.4<br>
        <span style="color: #10b981;">● 3.83M Transactions DWH</span>
    </div>
    """, unsafe_allow_html=True)


# ─── Routage & Affichage des Vues ────────────────────────────────────────────
try:
    if selected_view == "Overview":
        p1_overview.render_page(selected_year=selected_year, selected_store=selected_store)

    elif selected_view == "Store Performance":
        p2_stores.render_page(selected_year=selected_year, selected_store=selected_store)

    elif selected_view == "Sales Analytics":
        p3_sales.render_page(selected_year=selected_year, selected_store=selected_store)

    elif selected_view == "Products & Categories":
        p4_products.render_page(selected_year=selected_year, selected_store=selected_store)

    elif selected_view == "Customers & Loyalty":
        p5_customers.render_page(selected_year=selected_year, selected_store=selected_store)

    elif selected_view == "Inventory & Supply Chain":
        p6_inventory.render_page(selected_year=selected_year, selected_store=selected_store)

    elif selected_view == "Returns & Quality":
        p7_returns.render_page(selected_year=selected_year, selected_store=selected_store)

except Exception as e:
    st.error(f"Une erreur est survenue lors du chargement de la vue '{selected_view}' : {e}")
    st.info("Vérifiez la connexion au Data Warehouse PostgreSQL (port 5434).")
