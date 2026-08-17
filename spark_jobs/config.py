# =============================================================================
# RetailPlus — spark_jobs/config.py
# Configuration centralisée pour tous les jobs PySpark.
# =============================================================================

import os

# ─── Chemins du projet ────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_DIR      = os.path.join(PROJECT_ROOT, "data_generator", "output", "csv")

# ─── PostgreSQL — Data Warehouse ──────────────────────────────────────────────
# Lors de l'exécution depuis l'hôte Windows, le conteneur est accessible
# via localhost:5432. Depuis un conteneur Docker sur le même réseau,
# utiliser le nom du service 'postgres-dwh'.
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5434")

JDBC_URL   = f"jdbc:postgresql://{POSTGRES_HOST}:{POSTGRES_PORT}/retailplus"
JDBC_PROPS = {
    "user":     os.getenv("POSTGRES_USER",     "retailuser"),
    "password": os.getenv("POSTGRES_PASSWORD", "retailpassword"),
    "driver":   "org.postgresql.Driver",
}

# ─── Apache Kafka ─────────────────────────────────────────────────────────────
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPICS    = {
    "ventes":  "retailplus.ventes",
    "retours": "retailplus.retours",
}

# ─── Dépendances Maven pour les packages Spark ───────────────────────────────
# Ces packages sont téléchargés automatiquement par SparkSession.builder.
SPARK_PACKAGES = [
    "org.postgresql:postgresql:42.7.3",
    "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.9",
]

# ─── Règles de Validation & RegEx ─────────────────────────────────────────────
EMAIL_REGEX = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

# ─── Mapping CSV → Tables Bronze ─────────────────────────────────────────────
# Clé   = nom du fichier CSV (sans extension)
# Valeur = (table bronze cible, liste des colonnes à sélectionner depuis le CSV)
#
# Les colonnes « surrogates » (_sk) et les colonnes d'état (est_actif, date_creation, etc.)
# ne sont PAS dans le schéma bronze car la couche bronze stocke les données brutes
# sans transformation de typage fort ni de clés.
#
# La colonne « ingested_at » est ajoutée dynamiquement par le job PySpark
# lors de l'insertion (DEFAULT CURRENT_TIMESTAMP côté PostgreSQL).

REFERENTIELS_MAPPING: dict[str, tuple[str, list[str]]] = {
    "dim_magasin": (
        "bronze.dim_magasin",
        ["magasin_nk", "nom", "ville", "region", "type", "surface_m2"],
    ),
    "dim_fournisseur": (
        "bronze.dim_fournisseur",
        ["fournisseur_nk", "nom", "categorie_principale", "pays", "delai_livraison_jours"],
    ),
    "dim_produit": (
        "bronze.dim_produit",
        ["produit_nk", "nom", "categorie", "sous_categorie", "fournisseur_nk",
         "prix_achat_ht", "prix_vente_ht", "tva_pct", "prix_vente_ttc", "marge_brute_ht"],
    ),
    "dim_client": (
        "bronze.dim_client",
        ["client_nk", "prenom", "nom", "email", "telephone", "ville",
         "date_naissance", "date_inscription", "segment", "email_valide"],
    ),
    "dim_temps": (
        "bronze.dim_temps",
        ["temps_sk", "date_complete", "jour", "jour_semaine_num", "jour_semaine_nom",
         "semaine_annee", "mois_num", "mois_nom", "trimestre", "semestre", "annee",
         "est_weekend", "est_ferie", "est_jour_ouvre"],
    ),
}

TRANSACTIONS_MAPPING: dict[str, tuple[str, list[str]]] = {
    "fait_stock": (
        "bronze.fait_stock",
        ["date_snapshot", "produit_nk", "magasin_nk", "quantite_en_stock",
         "valeur_stock_ht", "seuil_reapprovisionnement", "en_rupture"],
    ),
    "fait_commandes": (
        "bronze.fait_commandes",
        ["commande_nk", "fournisseur_nk", "magasin_nk", "date_commande",
         "date_livraison_prev", "statut", "montant_total_ht"],
    ),
    "fait_lignes_commandes": (
        "bronze.fait_lignes_commandes",
        ["commande_nk", "produit_nk", "quantite_commandee",
         "prix_unitaire_achat", "montant_ligne_ht"],
    ),
    "fait_ventes": (
        "bronze.fait_ventes",
        ["ticket_nk", "timestamp_vente", "date_vente", "magasin_nk", "client_nk",
         "produit_nk", "quantite", "prix_unitaire_ht", "tva_pct",
         "prix_unitaire_ttc", "montant_ht", "montant_ttc",
         "marge_brute_unit", "marge_brute_total"],
    ),
    "fait_retours": (
        "bronze.fait_retours",
        ["retour_nk", "ticket_nk", "produit_nk", "magasin_nk", "client_nk",
         "date_vente_originale", "date_retour", "quantite_retournee",
         "montant_rembourse", "motif"],
    ),
}
