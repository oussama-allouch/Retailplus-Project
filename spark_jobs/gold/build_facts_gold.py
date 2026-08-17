# =============================================================================
# RetailPlus — spark_jobs/gold/build_facts_gold.py
# Alimentation des 4 tables de faits Gold avec résolution des clés de substitution (_sk)
# =============================================================================

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, date_format

from config import JDBC_URL, JDBC_PROPS
from utils.spark_session import get_spark_session


def build_gold_fait_stock(spark: SparkSession, dims: dict[str, DataFrame]) -> DataFrame:
    """Charge silver.fait_stock -> gold.fait_stock en mappant date_snapshot_sk, produit_sk et magasin_sk."""
    print("\n>> Alimentation de gold.fait_stock...")
    df_silver = spark.read.jdbc(url=JDBC_URL, table="silver.fait_stock", properties=JDBC_PROPS)

    df_prod_sk = dims["dim_produit"].select("produit_nk", "produit_sk")
    df_mag_sk  = dims["dim_magasin"].select("magasin_nk", "magasin_sk")

    j1 = df_silver.join(df_prod_sk, "produit_nk", "inner")
    j2 = j1.join(df_mag_sk, "magasin_nk", "inner")

    df_gold_input = j2.select(
        date_format(col("date_snapshot"), "yyyyMMdd").cast("int").alias("date_snapshot_sk"),
        col("produit_sk"),
        col("magasin_sk"),
        col("quantite_en_stock"),
        col("valeur_stock_ht"),
        col("seuil_reapprovisionnement"),
        col("en_rupture")
    )

    df_gold_input.write.jdbc(url=JDBC_URL, table="gold.fait_stock", mode="append", properties=JDBC_PROPS)

    count = spark.read.jdbc(url=JDBC_URL, table="gold.fait_stock", properties=JDBC_PROPS).count()
    print(f"   [OK] gold.fait_stock : {count:,} lignes inserees")
    return df_gold_input


def build_gold_fait_commandes(spark: SparkSession, dims: dict[str, DataFrame]) -> DataFrame:
    """Charge silver.fait_commandes -> gold.fait_commandes et retourne la table Gold avec commande_sk."""
    print("\n>> Alimentation de gold.fait_commandes...")
    df_silver = spark.read.jdbc(url=JDBC_URL, table="silver.fait_commandes", properties=JDBC_PROPS)

    df_fourn_sk = dims["dim_fournisseur"].select("fournisseur_nk", "fournisseur_sk")
    df_mag_sk   = dims["dim_magasin"].select("magasin_nk", "magasin_sk")

    j1 = df_silver.join(df_fourn_sk, "fournisseur_nk", "inner")
    j2 = j1.join(df_mag_sk, "magasin_nk", "inner")

    df_gold_input = j2.select(
        col("commande_nk"),
        col("fournisseur_sk"),
        col("magasin_sk"),
        date_format(col("date_commande"), "yyyyMMdd").cast("int").alias("date_commande_sk"),
        date_format(col("date_livraison_prev"), "yyyyMMdd").cast("int").alias("date_livraison_prev_sk"),
        col("statut"),
        col("montant_total_ht")
    )

    df_gold_input.write.jdbc(url=JDBC_URL, table="gold.fait_commandes", mode="append", properties=JDBC_PROPS)

    df_gold = spark.read.jdbc(url=JDBC_URL, table="gold.fait_commandes", properties=JDBC_PROPS)
    print(f"   [OK] gold.fait_commandes : {df_gold.count():,} lignes inserees")
    return df_gold


def build_gold_fait_lignes_commandes(spark: SparkSession, dims: dict[str, DataFrame], df_commandes_gold: DataFrame) -> DataFrame:
    """Charge silver.fait_lignes_commandes -> gold.fait_lignes_commandes."""
    print("\n>> Alimentation de gold.fait_lignes_commandes...")
    df_silver = spark.read.jdbc(url=JDBC_URL, table="silver.fait_lignes_commandes", properties=JDBC_PROPS)

    df_cmd_sk  = df_commandes_gold.select("commande_nk", "commande_sk")
    df_prod_sk = dims["dim_produit"].select("produit_nk", "produit_sk")

    j1 = df_silver.join(df_cmd_sk, "commande_nk", "inner")
    j2 = j1.join(df_prod_sk, "produit_nk", "inner")

    df_gold_input = j2.select(
        col("commande_sk"),
        col("produit_sk"),
        col("quantite_commandee"),
        col("prix_unitaire_achat"),
        col("montant_ligne_ht")
    )

    df_gold_input.write.jdbc(url=JDBC_URL, table="gold.fait_lignes_commandes", mode="append", properties=JDBC_PROPS)

    count = spark.read.jdbc(url=JDBC_URL, table="gold.fait_lignes_commandes", properties=JDBC_PROPS).count()
    print(f"   [OK] gold.fait_lignes_commandes : {count:,} lignes inserees")
    return df_gold_input


def build_gold_fait_ventes(spark: SparkSession, dims: dict[str, DataFrame]) -> DataFrame:
    """Charge silver.fait_ventes (~3.83M) -> gold.fait_ventes."""
    print("\n>> Alimentation de gold.fait_ventes (volumineux)...")
    t0 = time.time()
    df_silver = spark.read.jdbc(url=JDBC_URL, table="silver.fait_ventes", properties=JDBC_PROPS)

    df_mag_sk  = dims["dim_magasin"].select("magasin_nk", "magasin_sk")
    df_prod_sk = dims["dim_produit"].select("produit_nk", "produit_sk")
    df_cli_sk  = dims["dim_client"].select("client_nk", "client_sk")

    j1 = df_silver.join(df_mag_sk, "magasin_nk", "inner")
    j2 = j1.join(df_prod_sk, "produit_nk", "inner")
    j3 = j2.join(df_cli_sk, "client_nk", "left")

    df_gold_input = j3.select(
        col("ticket_nk"),
        col("timestamp_vente"),
        date_format(col("date_vente"), "yyyyMMdd").cast("int").alias("date_sk"),
        col("magasin_sk"),
        col("client_sk"),
        col("produit_sk"),
        col("quantite"),
        col("prix_unitaire_ht"),
        col("tva_pct"),
        col("prix_unitaire_ttc"),
        col("montant_ht"),
        col("montant_ttc"),
        col("marge_brute_unit"),
        col("marge_brute_total")
    )

    write_props = dict(JDBC_PROPS)
    write_props["batchsize"] = "10000"
    write_props["reWriteBatchedInserts"] = "true"

    df_repart = df_gold_input.repartition(8)
    df_repart.write.jdbc(url=JDBC_URL, table="gold.fait_ventes", mode="append", properties=write_props)

    count = spark.read.jdbc(url=JDBC_URL, table="gold.fait_ventes", properties=JDBC_PROPS).count()
    elapsed = time.time() - t0
    print(f"   [OK] gold.fait_ventes : {count:,} lignes inserees ({elapsed:.1f}s)")
    return df_gold_input


def build_gold_fait_retours(spark: SparkSession, dims: dict[str, DataFrame]) -> DataFrame:
    """Charge silver.fait_retours (~80K) -> gold.fait_retours."""
    print("\n>> Alimentation de gold.fait_retours...")
    df_silver = spark.read.jdbc(url=JDBC_URL, table="silver.fait_retours", properties=JDBC_PROPS)

    df_prod_sk = dims["dim_produit"].select("produit_nk", "produit_sk")
    df_mag_sk  = dims["dim_magasin"].select("magasin_nk", "magasin_sk")
    df_cli_sk  = dims["dim_client"].select("client_nk", "client_sk")

    j1 = df_silver.join(df_prod_sk, "produit_nk", "inner")
    j2 = j1.join(df_mag_sk, "magasin_nk", "inner")
    j3 = j2.join(df_cli_sk, "client_nk", "left")

    df_gold_input = j3.select(
        col("retour_nk"),
        col("ticket_nk"),
        col("produit_sk"),
        col("magasin_sk"),
        col("client_sk"),
        date_format(col("date_vente_originale"), "yyyyMMdd").cast("int").alias("date_vente_originale_sk"),
        date_format(col("date_retour"), "yyyyMMdd").cast("int").alias("date_retour_sk"),
        col("quantite_retournee"),
        col("montant_rembourse"),
        col("motif")
    )

    df_gold_input.write.jdbc(url=JDBC_URL, table="gold.fait_retours", mode="append", properties=JDBC_PROPS)

    count = spark.read.jdbc(url=JDBC_URL, table="gold.fait_retours", properties=JDBC_PROPS).count()
    print(f"   [OK] gold.fait_retours : {count:,} lignes inserees")
    return df_gold_input


def run_build_facts_gold(spark: SparkSession, dims: dict[str, DataFrame]) -> None:
    """Exécute l'alimentation ordonnée des 4 faits de la couche Gold."""
    print("=" * 70)
    print("  RetailPlus — Gold Layer : Population des Tables de Faits")
    print("=" * 70)

    t0 = time.time()
    build_gold_fait_stock(spark, dims)
    df_commandes_gold = build_gold_fait_commandes(spark, dims)
    build_gold_fait_lignes_commandes(spark, dims, df_commandes_gold)
    build_gold_fait_ventes(spark, dims)
    build_gold_fait_retours(spark, dims)

    print(f"\n[DONE] Tables de faits Gold alimentees avec succes en {time.time() - t0:.1f}s")


if __name__ == "__main__":
    from build_dimensions_gold import run_build_dimensions_gold
    spark = get_spark_session("RetailPlus-Gold-Facts", packages=["org.postgresql:postgresql:42.7.3"])
    dims = run_build_dimensions_gold(spark)
    run_build_facts_gold(spark, dims)
    spark.stop()
