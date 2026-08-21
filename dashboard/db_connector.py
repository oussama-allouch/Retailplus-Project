# =============================================================================
# RetailPlus — dashboard/db_connector.py
# Connecteur de base de données PostgreSQL Gold & Fonctions d'extraction
# =============================================================================

import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

# Paramètres de connexion PostgreSQL DWH
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5434")
DB_USER = os.getenv("POSTGRES_USER", "retailuser")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "retailpassword")
DB_NAME = os.getenv("POSTGRES_DB", "retailplus")

DB_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


@st.cache_resource
def get_engine():
    """Initialise et met en cache l'engine SQLAlchemy."""
    return create_engine(DB_URL, pool_pre_ping=True, pool_size=5, max_overflow=10)


def execute_query(query: str, params: dict = None) -> pd.DataFrame:
    """Exécute une requête SQL et retourne un DataFrame Pandas."""
    engine = get_engine()
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn, params=params)
    return df


@st.cache_data(ttl=600)
def get_kpis_globaux() -> pd.DataFrame:
    """Récupère les indicateurs clés globaux."""
    return execute_query("SELECT * FROM gold.vue_kpis_globaux;")


@st.cache_data(ttl=600)
def get_ventes_mensuelles() -> pd.DataFrame:
    """Récupère les ventes mensuelles par magasin."""
    return execute_query("""
        SELECT * FROM gold.vue_ventes_mensuelles 
        ORDER BY annee, mois_num;
    """)


@st.cache_data(ttl=600)
def get_performance_magasins() -> pd.DataFrame:
    """Récupère les métriques de performance des magasins."""
    return execute_query("SELECT * FROM gold.vue_performance_magasins ORDER BY chiffre_affaires_ttc DESC;")


@st.cache_data(ttl=600)
def get_performance_produits(limit: int = 50) -> pd.DataFrame:
    """Récupère les produits les plus performants."""
    return execute_query(f"SELECT * FROM gold.vue_performance_produits LIMIT {limit};")


@st.cache_data(ttl=600)
def get_ventes_par_categorie() -> pd.DataFrame:
    """Récupère le CA et les volumes agrégés par catégorie de produit."""
    return execute_query("""
        SELECT 
            categorie,
            COUNT(DISTINCT produit_sk) as nb_references,
            SUM(total_quantite_vendue) as quantite_vendue,
            SUM(chiffre_affaires_ttc)  as ca_ttc,
            SUM(marge_brute_totale)   as marge_totale,
            ROUND((SUM(marge_brute_totale) / NULLIF(SUM(chiffre_affaires_ttc) / 1.20, 0) * 100)::numeric, 2) as marge_pct
        FROM gold.vue_performance_produits
        GROUP BY categorie
        ORDER BY ca_ttc DESC;
    """)


@st.cache_data(ttl=600)
def get_segmentation_clients() -> pd.DataFrame:
    """Récupère les données de segmentation des clients."""
    return execute_query("""
        SELECT 
            segment,
            COUNT(client_sk) as nb_clients,
            SUM(nb_achats) as total_achats,
            SUM(depense_totale_ttc) as ca_total_ttc,
            ROUND(AVG(panier_moyen)::numeric, 2) as panier_moyen_segment,
            SUM(marge_totale_generee) as marge_totale
        FROM gold.vue_segmentation_clients
        GROUP BY segment
        ORDER BY ca_total_ttc DESC;
    """)


@st.cache_data(ttl=600)
def get_top_clients(limit: int = 20) -> pd.DataFrame:
    """Récupère le top clients par dépense."""
    return execute_query(f"SELECT * FROM gold.vue_segmentation_clients LIMIT {limit};")


@st.cache_data(ttl=600)
def get_gestion_stocks() -> pd.DataFrame:
    """Récupère les métriques de stocks et ruptures."""
    return execute_query("SELECT * FROM gold.vue_gestion_stocks;")


@st.cache_data(ttl=600)
def get_analyse_retours() -> pd.DataFrame:
    """Récupère l'analyse des retours par motif et catégorie."""
    return execute_query("SELECT * FROM gold.vue_analyse_retours;")
