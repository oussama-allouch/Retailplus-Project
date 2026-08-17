# =============================================================================
# RetailPlus — spark_jobs/silver/clean_transactions.py
# Pipeline Silver : Nettoyage, déduplication, typage et filtrage des anomalies
# pour les 5 tables de faits (bronze -> silver)
# =============================================================================

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, to_date, to_timestamp, trim, coalesce, lit

from config import JDBC_URL, JDBC_PROPS
from utils.spark_session import get_spark_session
from utils.quality_checks import split_rejected, filter_referential_integrity, write_rejected


def clean_fait_stock(spark: SparkSession, dims: dict[str, DataFrame]) -> DataFrame:
    """Nettoie bronze.fait_stock -> silver.fait_stock."""
    print("\n>> Nettoyage de bronze.fait_stock...")
    df_raw = spark.read.jdbc(url=JDBC_URL, table="bronze.fait_stock", properties=JDBC_PROPS)

    df_cleaned = df_raw.select(
        to_date(trim(col("date_snapshot"))).alias("date_snapshot"),
        trim(col("produit_nk")).alias("produit_nk"),
        trim(col("magasin_nk")).alias("magasin_nk"),
        col("quantite_en_stock").cast("int").alias("quantite_en_stock"),
        col("valeur_stock_ht").cast("decimal(12,2)").alias("valeur_stock_ht"),
        col("seuil_reapprovisionnement").cast("int").alias("seuil_reapprovisionnement"),
        col("en_rupture").cast("boolean").alias("en_rupture")
    )

    invalid_cond = (
        col("date_snapshot").isNull() |
        col("produit_nk").isNull() |
        col("magasin_nk").isNull() |
        col("quantite_en_stock").isNull() |
        (col("quantite_en_stock") < 0)
    )
    df_valid, df_rej = split_rejected(df_cleaned, invalid_cond, "fait_stock", "Date/Produit/Magasin NULL ou stock negatif")
    num_rej = write_rejected(df_rej)

    # Intégrité référentielle FK produit et magasin
    df_valid, df_rej_prod = filter_referential_integrity(df_valid, dims["dim_produit"], "produit_nk", "produit_nk", "fait_stock", "produit_nk inexistant")
    num_rej += write_rejected(df_rej_prod)

    df_valid, df_rej_mag = filter_referential_integrity(df_valid, dims["dim_magasin"], "magasin_nk", "magasin_nk", "fait_stock", "magasin_nk inexistant")
    num_rej += write_rejected(df_rej_mag)

    df_dedup = df_valid.dropDuplicates(["date_snapshot", "produit_nk", "magasin_nk"])
    df_dedup.write.jdbc(url=JDBC_URL, table="silver.fait_stock", mode="append", properties=JDBC_PROPS)
    print(f"   [OK] silver.fait_stock : {df_dedup.count()} lignes inserees ({num_rej} rejets)")
    return df_dedup


def clean_fait_commandes(spark: SparkSession, dims: dict[str, DataFrame]) -> DataFrame:
    """Nettoie bronze.fait_commandes -> silver.fait_commandes."""
    print("\n>> Nettoyage de bronze.fait_commandes...")
    df_raw = spark.read.jdbc(url=JDBC_URL, table="bronze.fait_commandes", properties=JDBC_PROPS)

    df_cleaned = df_raw.select(
        trim(col("commande_nk")).alias("commande_nk"),
        trim(col("fournisseur_nk")).alias("fournisseur_nk"),
        trim(col("magasin_nk")).alias("magasin_nk"),
        to_date(trim(col("date_commande"))).alias("date_commande"),
        to_date(trim(col("date_livraison_prev"))).alias("date_livraison_prev"),
        trim(col("statut")).alias("statut"),
        col("montant_total_ht").cast("decimal(12,2)").alias("montant_total_ht")
    )

    invalid_cond = (
        col("commande_nk").isNull() |
        col("fournisseur_nk").isNull() |
        col("magasin_nk").isNull() |
        col("date_commande").isNull() |
        col("montant_total_ht").isNull() |
        (col("montant_total_ht") < 0)
    )
    df_valid, df_rej = split_rejected(df_cleaned, invalid_cond, "fait_commandes", "Champ obligatoire NULL ou montant negatif")
    num_rej = write_rejected(df_rej)

    df_valid, df_rej_fourn = filter_referential_integrity(df_valid, dims["dim_fournisseur"], "fournisseur_nk", "fournisseur_nk", "fait_commandes", "fournisseur_nk inexistant")
    num_rej += write_rejected(df_rej_fourn)

    df_valid, df_rej_mag = filter_referential_integrity(df_valid, dims["dim_magasin"], "magasin_nk", "magasin_nk", "fait_commandes", "magasin_nk inexistant")
    num_rej += write_rejected(df_rej_mag)

    df_dedup = df_valid.dropDuplicates(["commande_nk"])
    df_dedup.write.jdbc(url=JDBC_URL, table="silver.fait_commandes", mode="append", properties=JDBC_PROPS)
    print(f"   [OK] silver.fait_commandes : {df_dedup.count()} lignes inserees ({num_rej} rejets)")
    return df_dedup


def clean_fait_lignes_commandes(spark: SparkSession, dims: dict[str, DataFrame], df_commandes: DataFrame) -> DataFrame:
    """Nettoie bronze.fait_lignes_commandes -> silver.fait_lignes_commandes."""
    print("\n>> Nettoyage de bronze.fait_lignes_commandes...")
    df_raw = spark.read.jdbc(url=JDBC_URL, table="bronze.fait_lignes_commandes", properties=JDBC_PROPS)

    df_cleaned = df_raw.select(
        trim(col("commande_nk")).alias("commande_nk"),
        trim(col("produit_nk")).alias("produit_nk"),
        col("quantite_commandee").cast("int").alias("quantite_commandee"),
        col("prix_unitaire_achat").cast("decimal(12,2)").alias("prix_unitaire_achat"),
        col("montant_ligne_ht").cast("decimal(12,2)").alias("montant_ligne_ht")
    )

    invalid_cond = (
        col("commande_nk").isNull() |
        col("produit_nk").isNull() |
        col("quantite_commandee").isNull() | (col("quantite_commandee") <= 0) |
        col("prix_unitaire_achat").isNull() | (col("prix_unitaire_achat") < 0)
    )
    df_valid, df_rej = split_rejected(df_cleaned, invalid_cond, "fait_lignes_commandes", "Quantite/Prix invalide ou clé NULL")
    num_rej = write_rejected(df_rej)

    df_valid, df_rej_cmd = filter_referential_integrity(df_valid, df_commandes, "commande_nk", "commande_nk", "fait_lignes_commandes", "commande_nk inexistante")
    num_rej += write_rejected(df_rej_cmd)

    df_valid, df_rej_prod = filter_referential_integrity(df_valid, dims["dim_produit"], "produit_nk", "produit_nk", "fait_lignes_commandes", "produit_nk inexistant")
    num_rej += write_rejected(df_rej_prod)

    df_dedup = df_valid.dropDuplicates(["commande_nk", "produit_nk"])
    df_dedup.write.jdbc(url=JDBC_URL, table="silver.fait_lignes_commandes", mode="append", properties=JDBC_PROPS)
    print(f"   [OK] silver.fait_lignes_commandes : {df_dedup.count()} lignes inserees ({num_rej} rejets)")
    return df_dedup


def clean_fait_ventes(spark: SparkSession, dims: dict[str, DataFrame]) -> DataFrame:
    """
    Nettoie bronze.fait_ventes (~4.25M lignes) -> silver.fait_ventes.
    Filtre les quantites <= 0, prix/montants < 0, doublons et FKs orphelines.
    """
    print("\n>> Nettoyage de bronze.fait_ventes (volumineux)...")
    t0 = time.time()
    df_raw = spark.read.jdbc(url=JDBC_URL, table="bronze.fait_ventes", properties=JDBC_PROPS)

    # Calculs de secours pour les colonnes optionnelles en streaming Kafka
    tva_val = coalesce(col("tva_pct").cast("decimal(5,2)"), lit(20.00))
    pu_ttc  = col("prix_unitaire_ttc").cast("decimal(12,2)")
    pu_ht   = coalesce(col("prix_unitaire_ht").cast("decimal(12,2)"), (pu_ttc / lit(1.20)).cast("decimal(12,2)"))
    m_ttc   = col("montant_ttc").cast("decimal(12,2)")
    m_ht    = coalesce(col("montant_ht").cast("decimal(12,2)"), (m_ttc / lit(1.20)).cast("decimal(12,2)"))
    marge_u = coalesce(col("marge_brute_unit").cast("decimal(12,2)"), (pu_ht * lit(0.20)).cast("decimal(12,2)"))
    marge_t = coalesce(col("marge_brute_total").cast("decimal(12,2)"), (marge_u * col("quantite").cast("int")).cast("decimal(12,2)"))

    df_cleaned = df_raw.select(
        trim(col("ticket_nk")).alias("ticket_nk"),
        to_timestamp(trim(col("timestamp_vente"))).alias("timestamp_vente"),
        coalesce(to_date(trim(col("date_vente"))), to_date(trim(col("timestamp_vente")))).alias("date_vente"),
        trim(col("magasin_nk")).alias("magasin_nk"),
        trim(col("client_nk")).alias("client_nk"),
        trim(col("produit_nk")).alias("produit_nk"),
        col("quantite").cast("int").alias("quantite"),
        pu_ht.alias("prix_unitaire_ht"),
        tva_val.alias("tva_pct"),
        pu_ttc.alias("prix_unitaire_ttc"),
        m_ht.alias("montant_ht"),
        m_ttc.alias("montant_ttc"),
        marge_u.alias("marge_brute_unit"),
        marge_t.alias("marge_brute_total")
    )

    # 1. Filtrage des anomalies métier : quantités <= 0 ou montants < 0
    invalid_cond = (
        col("ticket_nk").isNull() |
        col("produit_nk").isNull() |
        col("magasin_nk").isNull() |
        col("timestamp_vente").isNull() |
        col("quantite").isNull() | (col("quantite") <= 0) |
        col("montant_ttc").isNull() | (col("montant_ttc") < 0)
    )
    df_valid, df_rej = split_rejected(df_cleaned, invalid_cond, "fait_ventes", "Quantite <= 0 ou montant TTC negatif")
    num_rej = write_rejected(df_rej)

    # 2. Intégrité référentielle FK
    df_valid, df_rej_mag = filter_referential_integrity(df_valid, dims["dim_magasin"], "magasin_nk", "magasin_nk", "fait_ventes", "magasin_nk inexistant")
    num_rej += write_rejected(df_rej_mag)

    df_valid, df_rej_prod = filter_referential_integrity(df_valid, dims["dim_produit"], "produit_nk", "produit_nk", "fait_ventes", "produit_nk inexistant")
    num_rej += write_rejected(df_rej_prod)

    # Pour client_nk: autorisé NULL, mais si présent doit exister dans dim_client (reject ghost clients)
    df_valid, df_rej_cli = filter_referential_integrity(df_valid, dims["dim_client"], "client_nk", "client_nk", "fait_ventes", "client_nk fantome inexistant", allow_null_fk=True)
    num_rej += write_rejected(df_rej_cli)

    # 3. Déduplication sur (ticket_nk, produit_nk)
    df_dedup = df_valid.dropDuplicates(["ticket_nk", "produit_nk"])

    # 4. Écriture partitionnée dans PostgreSQL
    write_props = dict(JDBC_PROPS)
    write_props["batchsize"] = "10000"
    write_props["reWriteBatchedInserts"] = "true"

    df_dedup_repart = df_dedup.repartition(8)
    df_dedup_repart.write.jdbc(url=JDBC_URL, table="silver.fait_ventes", mode="append", properties=write_props)
    
    elapsed = time.time() - t0
    print(f"   [OK] silver.fait_ventes : {df_dedup.count():,} lignes inserees ({num_rej:,} rejets, {elapsed:.1f}s)")
    return df_dedup


def clean_fait_retours(spark: SparkSession, dims: dict[str, DataFrame]) -> DataFrame:
    """Nettoie bronze.fait_retours -> silver.fait_retours."""
    print("\n>> Nettoyage de bronze.fait_retours...")
    df_raw = spark.read.jdbc(url=JDBC_URL, table="bronze.fait_retours", properties=JDBC_PROPS)

    df_cleaned = df_raw.select(
        trim(col("retour_nk")).alias("retour_nk"),
        trim(col("ticket_nk")).alias("ticket_nk"),
        trim(col("produit_nk")).alias("produit_nk"),
        trim(col("magasin_nk")).alias("magasin_nk"),
        trim(col("client_nk")).alias("client_nk"),
        coalesce(to_date(trim(col("date_vente_originale"))), to_date(trim(col("date_retour")))).alias("date_vente_originale"),
        to_date(trim(col("date_retour"))).alias("date_retour"),
        col("quantite_retournee").cast("int").alias("quantite_retournee"),
        col("montant_rembourse").cast("decimal(12,2)").alias("montant_rembourse"),
        trim(col("motif")).alias("motif")
    )

    invalid_cond = (
        col("retour_nk").isNull() |
        col("ticket_nk").isNull() |
        col("produit_nk").isNull() |
        col("magasin_nk").isNull() |
        col("date_retour").isNull() |
        col("quantite_retournee").isNull() | (col("quantite_retournee") <= 0)
    )
    df_valid, df_rej = split_rejected(df_cleaned, invalid_cond, "fait_retours", "Retour_nk/Produit NULL ou quantite <= 0")
    num_rej = write_rejected(df_rej)

    df_valid, df_rej_prod = filter_referential_integrity(df_valid, dims["dim_produit"], "produit_nk", "produit_nk", "fait_retours", "produit_nk inexistant")
    num_rej += write_rejected(df_rej_prod)

    df_valid, df_rej_mag = filter_referential_integrity(df_valid, dims["dim_magasin"], "magasin_nk", "magasin_nk", "fait_retours", "magasin_nk inexistant")
    num_rej += write_rejected(df_rej_mag)

    df_valid, df_rej_cli = filter_referential_integrity(df_valid, dims["dim_client"], "client_nk", "client_nk", "fait_retours", "client_nk fantome inexistant", allow_null_fk=True)
    num_rej += write_rejected(df_rej_cli)

    df_dedup = df_valid.dropDuplicates(["retour_nk"])
    df_dedup.write.jdbc(url=JDBC_URL, table="silver.fait_retours", mode="append", properties=JDBC_PROPS)
    print(f"   [OK] silver.fait_retours : {df_dedup.count():,} lignes inserees ({num_rej:,} rejets)")
    return df_dedup


def run_clean_transactions(spark: SparkSession, dims: dict[str, DataFrame]) -> None:
    """Exécute le nettoyage complet des 5 tables de faits."""
    print("=" * 70)
    print("  RetailPlus — Silver Layer : Nettoyage des Transactions (Faits)")
    print("=" * 70)

    t0 = time.time()
    clean_fait_stock(spark, dims)
    df_commandes = clean_fait_commandes(spark, dims)
    clean_fait_lignes_commandes(spark, dims, df_commandes)
    clean_fait_ventes(spark, dims)
    clean_fait_retours(spark, dims)

    print(f"\n[DONE] Nettoyage des faits termine en {time.time() - t0:.1f}s")


if __name__ == "__main__":
    from clean_dimensions import run_clean_dimensions
    spark = get_spark_session("RetailPlus-Silver-Transactions", packages=["org.postgresql:postgresql:42.7.3"])
    dims = run_clean_dimensions(spark)
    run_clean_transactions(spark, dims)
    spark.stop()
