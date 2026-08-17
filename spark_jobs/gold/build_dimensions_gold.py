# =============================================================================
# RetailPlus — spark_jobs/gold/build_dimensions_gold.py
# Chargement des 5 dimensions dans le schéma Gold (Data Warehouse)
# Génération automatique des clés de substitution (_sk) et résolution des FK
# =============================================================================

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col

from config import JDBC_URL, JDBC_PROPS
from utils.spark_session import get_spark_session


def build_gold_dim_magasin(spark: SparkSession) -> DataFrame:
    """Charge silver.dim_magasin -> gold.dim_magasin et retourne le mapping (_nk, _sk)."""
    print("\n>> Alimentation de gold.dim_magasin...")
    df_silver = spark.read.jdbc(url=JDBC_URL, table="silver.dim_magasin", properties=JDBC_PROPS)

    df_gold_input = df_silver.select(
        col("magasin_nk"),
        col("nom"),
        col("ville"),
        col("region"),
        col("type"),
        col("surface_m2")
    )

    df_gold_input.write.jdbc(url=JDBC_URL, table="gold.dim_magasin", mode="append", properties=JDBC_PROPS)

    # Re-lecture depuis PostgreSQL pour récupérer les clés de substitution SERIAL générées
    df_gold = spark.read.jdbc(url=JDBC_URL, table="gold.dim_magasin", properties=JDBC_PROPS)
    print(f"   [OK] gold.dim_magasin : {df_gold.count()} lignes inserees")
    return df_gold


def build_gold_dim_fournisseur(spark: SparkSession) -> DataFrame:
    """Charge silver.dim_fournisseur -> gold.dim_fournisseur et retourne le mapping (_nk, _sk)."""
    print("\n>> Alimentation de gold.dim_fournisseur...")
    df_silver = spark.read.jdbc(url=JDBC_URL, table="silver.dim_fournisseur", properties=JDBC_PROPS)

    df_gold_input = df_silver.select(
        col("fournisseur_nk"),
        col("nom"),
        col("categorie_principale"),
        col("pays"),
        col("delai_livraison_jours")
    )

    df_gold_input.write.jdbc(url=JDBC_URL, table="gold.dim_fournisseur", mode="append", properties=JDBC_PROPS)

    df_gold = spark.read.jdbc(url=JDBC_URL, table="gold.dim_fournisseur", properties=JDBC_PROPS)
    print(f"   [OK] gold.dim_fournisseur : {df_gold.count()} lignes inserees")
    return df_gold


def build_gold_dim_produit(spark: SparkSession, df_fournisseur_gold: DataFrame) -> DataFrame:
    """Charge silver.dim_produit -> gold.dim_produit en résolvant la FK fournisseur_sk."""
    print("\n>> Alimentation de gold.dim_produit...")
    df_silver = spark.read.jdbc(url=JDBC_URL, table="silver.dim_produit", properties=JDBC_PROPS)

    # Resolution de la clé fournisseur_sk via join sur fournisseur_nk
    df_fourn_keys = df_fournisseur_gold.select("fournisseur_nk", "fournisseur_sk")
    joined = df_silver.join(df_fourn_keys, "fournisseur_nk", "left")

    df_gold_input = joined.select(
        col("produit_nk"),
        col("nom"),
        col("categorie"),
        col("sous_categorie"),
        col("fournisseur_sk"),
        col("prix_achat_ht"),
        col("prix_vente_ht"),
        col("tva_pct"),
        col("prix_vente_ttc"),
        col("marge_brute_ht")
    )

    df_gold_input.write.jdbc(url=JDBC_URL, table="gold.dim_produit", mode="append", properties=JDBC_PROPS)

    df_gold = spark.read.jdbc(url=JDBC_URL, table="gold.dim_produit", properties=JDBC_PROPS)
    print(f"   [OK] gold.dim_produit : {df_gold.count()} lignes inserees")
    return df_gold


def build_gold_dim_client(spark: SparkSession) -> DataFrame:
    """Charge silver.dim_client -> gold.dim_client et retourne le mapping (_nk, _sk)."""
    print("\n>> Alimentation de gold.dim_client...")
    df_silver = spark.read.jdbc(url=JDBC_URL, table="silver.dim_client", properties=JDBC_PROPS)

    df_gold_input = df_silver.select(
        col("client_nk"),
        col("prenom"),
        col("nom"),
        col("email"),
        col("telephone"),
        col("ville"),
        col("date_naissance"),
        col("date_inscription"),
        col("segment")
    )

    df_gold_input.write.jdbc(url=JDBC_URL, table="gold.dim_client", mode="append", properties=JDBC_PROPS)

    df_gold = spark.read.jdbc(url=JDBC_URL, table="gold.dim_client", properties=JDBC_PROPS)
    print(f"   [OK] gold.dim_client : {df_gold.count()} lignes inserees")
    return df_gold


def build_gold_dim_temps(spark: SparkSession) -> DataFrame:
    """Génère et alimente la dimension temps complète (2024-2030) dans gold.dim_temps avec Spark SQL."""
    print("\n>> Alimentation de gold.dim_temps (2024-2030)...")

    df_dates = spark.sql("""
        SELECT explode(sequence(to_date('2024-01-01'), to_date('2030-12-31'), interval 1 day)) as date_complete
    """)

    df_temps = df_dates.selectExpr(
        "cast(date_format(date_complete, 'yyyyMMdd') as int) as temps_sk",
        "date_complete",
        "day(date_complete) as jour",
        "dayofweek(date_complete) as jour_semaine_num",
        "date_format(date_complete, 'EEEE') as jour_semaine_nom",
        "weekofyear(date_complete) as semaine_annee",
        "month(date_complete) as mois_num",
        "date_format(date_complete, 'MMMM') as mois_nom",
        "quarter(date_complete) as trimestre",
        "case when month(date_complete) <= 6 then 1 else 2 end as semestre",
        "year(date_complete) as annee",
        "case when dayofweek(date_complete) in (1, 7) then true else false end as est_weekend",
        "false as est_ferie",
        "case when dayofweek(date_complete) in (1, 7) then false else true end as est_jour_ouvre"
    )

    df_temps.write.jdbc(url=JDBC_URL, table="gold.dim_temps", mode="append", properties=JDBC_PROPS)

    df_gold = spark.read.jdbc(url=JDBC_URL, table="gold.dim_temps", properties=JDBC_PROPS)
    print(f"   [OK] gold.dim_temps : {df_gold.count()} lignes inserees (2024-2030)")
    return df_gold


def run_build_dimensions_gold(spark: SparkSession) -> dict[str, DataFrame]:
    """Exécute l'alimentation ordonnée des 5 dimensions de la couche Gold."""
    print("=" * 70)
    print("  RetailPlus — Gold Layer : Population des Dimensions (Star Schema)")
    print("=" * 70)

    t0 = time.time()
    df_magasin     = build_gold_dim_magasin(spark)
    df_fournisseur = build_gold_dim_fournisseur(spark)
    df_produit     = build_gold_dim_produit(spark, df_fournisseur)
    df_client      = build_gold_dim_client(spark)
    df_temps       = build_gold_dim_temps(spark)

    print(f"\n[DONE] Dimensions Gold alimentees avec succes en {time.time() - t0:.1f}s")

    return {
        "dim_magasin": df_magasin,
        "dim_fournisseur": df_fournisseur,
        "dim_produit": df_produit,
        "dim_client": df_client,
        "dim_temps": df_temps,
    }


if __name__ == "__main__":
    spark = get_spark_session("RetailPlus-Gold-Dimensions", packages=["org.postgresql:postgresql:42.7.3"])
    run_build_dimensions_gold(spark)
    spark.stop()
