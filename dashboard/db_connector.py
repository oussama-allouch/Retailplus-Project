# =============================================================================
# RetailPlus — dashboard/db_connector.py
# Connecteur de base de données PostgreSQL Gold & Fonctions d'extraction
# =============================================================================

import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

# ─── Paramètres de connexion PostgreSQL DWH ──────────────────────────────────
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5434")
DB_USER = os.getenv("POSTGRES_USER", "retailuser")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "retailpassword")
DB_NAME = os.getenv("POSTGRES_DB", "retailplus")

DB_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


@st.cache_resource
def get_engine():
    """Initialise et met en cache l'engine SQLAlchemy avec pool de connexions."""
    return create_engine(DB_URL, pool_pre_ping=True, pool_size=5, max_overflow=10)


def execute_query(query: str, params: dict = None) -> pd.DataFrame:
    """Exécute une requête SQL de manière sécurisée et retourne un DataFrame Pandas."""
    engine = get_engine()
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params=params)
        return df
    except Exception as e:
        st.error(f"Erreur d'accès à la base de données : {e}")
        return pd.DataFrame()


# ─── Fonctions d'Extraction Analytique (avec filtres & cache) ──────────────────

@st.cache_data(ttl=600)
def get_annees_disponibles() -> list[int]:
    """Récupère les années disponibles dans les ventes."""
    df = execute_query("SELECT DISTINCT annee FROM gold.vue_ventes_mensuelles ORDER BY annee DESC;")
    if not df.empty and "annee" in df.columns:
        return [int(a) for a in df["annee"].tolist()]
    return [2024]


@st.cache_data(ttl=600)
def get_kpis_globaux(year: int = None, store: str = None) -> pd.DataFrame:
    """Récupère les indicateurs clés globaux avec filtrage optionnel par année et magasin."""
    if year is None and store is None:
        return execute_query("SELECT * FROM gold.vue_kpis_globaux;")
    
    # Calcul dynamique à partir des ventes mensuelles si un filtre est appliqué
    conditions = []
    params = {}
    if year:
        conditions.append("annee = :year")
        params["year"] = year
    if store and store != "Tous les magasins":
        conditions.append("magasin_nom = :store")
        params["store"] = store
        
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    
    query = f"""
        SELECT 
            SUM(total_transactions)                                      AS total_transactions,
            SUM(articles_vendus)                                         AS total_articles_vendus,
            ROUND(SUM(chiffre_affaires_ttc)::numeric, 2)                 AS chiffre_affaires_ttc,
            ROUND(SUM(chiffre_affaires_ht)::numeric, 2)                  AS chiffre_affaires_ht,
            ROUND(SUM(marge_brute_totale)::numeric, 2)                   AS marge_brute_totale,
            ROUND((SUM(marge_brute_totale) / NULLIF(SUM(chiffre_affaires_ht), 0) * 100)::numeric, 2) AS taux_marge_pct,
            ROUND((SUM(chiffre_affaires_ttc) / NULLIF(SUM(total_transactions), 0))::numeric, 2) AS panier_moyen_ttc,
            COUNT(DISTINCT magasin_sk)                                   AS total_magasins,
            10000                                                        AS clients_actifs
        FROM gold.vue_ventes_mensuelles
        {where_clause};
    """
    return execute_query(query, params)


@st.cache_data(ttl=600)
def get_ventes_mensuelles(year: int = None, store: str = None) -> pd.DataFrame:
    """Récupère l'historique mensuel des ventes filtré par année et magasin."""
    conditions = []
    params = {}
    if year:
        conditions.append("annee = :year")
        params["year"] = year
    if store and store != "Tous les magasins":
        conditions.append("magasin_nom = :store")
        params["store"] = store

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    query = f"""
        SELECT * FROM gold.vue_ventes_mensuelles
        {where_clause}
        ORDER BY annee, mois_num;
    """
    return execute_query(query, params)


@st.cache_data(ttl=600)
def get_performance_magasins() -> pd.DataFrame:
    """Récupère les métriques comparatives des 5 magasins physiques."""
    return execute_query("SELECT * FROM gold.vue_performance_magasins ORDER BY chiffre_affaires_ttc DESC;")


@st.cache_data(ttl=600)
def get_performance_produits(limit: int = 50, category: str = None) -> pd.DataFrame:
    """Récupère les produits les plus performants avec filtrage par catégorie."""
    if category and category != "Toutes les catégories":
        query = f"SELECT * FROM gold.vue_performance_produits WHERE categorie = :cat ORDER BY chiffre_affaires_ttc DESC LIMIT {limit};"
        return execute_query(query, {"cat": category})
    return execute_query(f"SELECT * FROM gold.vue_performance_produits ORDER BY chiffre_affaires_ttc DESC LIMIT {limit};")


@st.cache_data(ttl=600)
def get_ventes_par_categorie() -> pd.DataFrame:
    """Récupère les ventes agrégées par catégorie de produit."""
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
    """Récupère les métriques de segmentation RFM."""
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
def get_clients_par_ville() -> pd.DataFrame:
    """Récupère la répartition géographique des clients par ville."""
    return execute_query("""
        SELECT 
            client_ville as ville,
            COUNT(client_sk) as nb_clients,
            SUM(depense_totale_ttc) as ca_total_ttc,
            ROUND(AVG(panier_moyen)::numeric, 2) as panier_moyen_ville
        FROM gold.vue_segmentation_clients
        GROUP BY client_ville
        ORDER BY ca_total_ttc DESC;
    """)


@st.cache_data(ttl=600)
def get_top_clients(limit: int = 20) -> pd.DataFrame:
    """Récupère le top clients par montant dépensé."""
    return execute_query(f"SELECT * FROM gold.vue_segmentation_clients ORDER BY depense_totale_ttc DESC LIMIT {limit};")


@st.cache_data(ttl=600)
def get_gestion_stocks() -> pd.DataFrame:
    """Récupère les métriques de stocks, réapprovisionnement et fournisseurs."""
    return execute_query("SELECT * FROM gold.vue_gestion_stocks;")


@st.cache_data(ttl=600)
def get_analyse_retours() -> pd.DataFrame:
    """Récupère l'analyse des retours d'articles."""
    return execute_query("SELECT * FROM gold.vue_analyse_retours;")
