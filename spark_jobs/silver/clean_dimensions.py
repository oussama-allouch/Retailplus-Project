# =============================================================================
# RetailPlus — spark_jobs/silver/clean_dimensions.py
# Pipeline Silver : Nettoyage, déduplication et typage des 5 dimensions
# (bronze -> silver)
# =============================================================================

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, when, regexp_extract, to_date, trim

from config import JDBC_URL, JDBC_PROPS, EMAIL_REGEX
from utils.spark_session import get_spark_session
from utils.quality_checks import split_rejected, filter_referential_integrity, write_rejected


def clean_dim_magasin(spark: SparkSession) -> DataFrame:
    """Nettoie bronze.dim_magasin -> silver.dim_magasin."""
    print("\n>> Nettoyage de bronze.dim_magasin...")
    df_raw = spark.read.jdbc(url=JDBC_URL, table="bronze.dim_magasin", properties=JDBC_PROPS)

    # 1. Nettoyage des espaces et cast des types
    df_cleaned = df_raw.select(
        trim(col("magasin_nk")).alias("magasin_nk"),
        trim(col("nom")).alias("nom"),
        trim(col("ville")).alias("ville"),
        trim(col("region")).alias("region"),
        trim(col("type")).alias("type"),
        col("surface_m2").cast("int").alias("surface_m2")
    )

    # 2. Validation des valeurs obligatoires
    invalid_cond = (
        col("magasin_nk").isNull() |
        col("nom").isNull() |
        col("ville").isNull() |
        col("region").isNull() |
        col("type").isNull() |
        col("surface_m2").isNull() |
        (col("surface_m2") <= 0)
    )
    df_valid, df_rej = split_rejected(df_cleaned, invalid_cond, "dim_magasin", "Champ obligatoire NULL ou surface invalide")
    num_rej = write_rejected(df_rej)

    # 3. Déduplication sur la clé naturelle
    df_dedup = df_valid.dropDuplicates(["magasin_nk"])

    # 4. Écriture dans PostgreSQL silver.dim_magasin
    df_dedup.write.jdbc(url=JDBC_URL, table="silver.dim_magasin", mode="append", properties=JDBC_PROPS)
    print(f"   [OK] silver.dim_magasin : {df_dedup.count()} lignes inserees ({num_rej} rejets)")
    return df_dedup


def clean_dim_fournisseur(spark: SparkSession) -> DataFrame:
    """Nettoie bronze.dim_fournisseur -> silver.dim_fournisseur."""
    print("\n>> Nettoyage de bronze.dim_fournisseur...")
    df_raw = spark.read.jdbc(url=JDBC_URL, table="bronze.dim_fournisseur", properties=JDBC_PROPS)

    df_cleaned = df_raw.select(
        trim(col("fournisseur_nk")).alias("fournisseur_nk"),
        trim(col("nom")).alias("nom"),
        trim(col("categorie_principale")).alias("categorie_principale"),
        trim(col("pays")).alias("pays"),
        col("delai_livraison_jours").cast("int").alias("delai_livraison_jours")
    )

    invalid_cond = (
        col("fournisseur_nk").isNull() |
        col("nom").isNull() |
        col("categorie_principale").isNull() |
        col("pays").isNull() |
        col("delai_livraison_jours").isNull() |
        (col("delai_livraison_jours") < 0)
    )
    df_valid, df_rej = split_rejected(df_cleaned, invalid_cond, "dim_fournisseur", "Champ obligatoire NULL ou delai invalide")
    num_rej = write_rejected(df_rej)

    df_dedup = df_valid.dropDuplicates(["fournisseur_nk"])
    df_dedup.write.jdbc(url=JDBC_URL, table="silver.dim_fournisseur", mode="append", properties=JDBC_PROPS)
    print(f"   [OK] silver.dim_fournisseur : {df_dedup.count()} lignes inserees ({num_rej} rejets)")
    return df_dedup


def clean_dim_produit(spark: SparkSession, df_fournisseur: DataFrame) -> DataFrame:
    """Nettoie bronze.dim_produit -> silver.dim_produit (nécessite silver.dim_fournisseur pour valider la FK)."""
    print("\n>> Nettoyage de bronze.dim_produit...")
    df_raw = spark.read.jdbc(url=JDBC_URL, table="bronze.dim_produit", properties=JDBC_PROPS)

    df_cleaned = df_raw.select(
        trim(col("produit_nk")).alias("produit_nk"),
        trim(col("nom")).alias("nom"),
        trim(col("categorie")).alias("categorie"),
        trim(col("sous_categorie")).alias("sous_categorie"),
        trim(col("fournisseur_nk")).alias("fournisseur_nk"),
        col("prix_achat_ht").cast("decimal(12,2)").alias("prix_achat_ht"),
        col("prix_vente_ht").cast("decimal(12,2)").alias("prix_vente_ht"),
        col("tva_pct").cast("decimal(5,2)").alias("tva_pct"),
        col("prix_vente_ttc").cast("decimal(12,2)").alias("prix_vente_ttc"),
        col("marge_brute_ht").cast("decimal(12,2)").alias("marge_brute_ht")
    )

    # Validation des prix et valeurs obligatoires
    invalid_cond = (
        col("produit_nk").isNull() |
        col("nom").isNull() |
        col("categorie").isNull() |
        col("fournisseur_nk").isNull() |
        col("prix_achat_ht").isNull() | (col("prix_achat_ht") < 0) |
        col("prix_vente_ht").isNull() | (col("prix_vente_ht") < 0) |
        col("prix_vente_ttc").isNull() | (col("prix_vente_ttc") < 0)
    )
    df_valid, df_rej = split_rejected(df_cleaned, invalid_cond, "dim_produit", "Prix invalide ou champ obligatoire NULL")
    num_rej = write_rejected(df_rej)

    # Intégrité référentielle FK fournisseur_nk -> dim_fournisseur
    df_valid_fk, df_rej_fk = filter_referential_integrity(
        df_valid, df_fournisseur, "fournisseur_nk", "fournisseur_nk", "dim_produit", "fournisseur_nk inexistant"
    )
    num_rej += write_rejected(df_rej_fk)

    df_dedup = df_valid_fk.dropDuplicates(["produit_nk"])
    df_dedup.write.jdbc(url=JDBC_URL, table="silver.dim_produit", mode="append", properties=JDBC_PROPS)
    print(f"   [OK] silver.dim_produit : {df_dedup.count()} lignes inserees ({num_rej} rejets)")
    return df_dedup


def clean_dim_client(spark: SparkSession) -> DataFrame:
    """Nettoie bronze.dim_client -> silver.dim_client."""
    print("\n>> Nettoyage de bronze.dim_client...")
    df_raw = spark.read.jdbc(url=JDBC_URL, table="bronze.dim_client", properties=JDBC_PROPS)

    # Validation de l'email : si invalide selon EMAIL_REGEX, on le passe à NULL (sans rejeter le client)
    email_clean = when(
        col("email").rlike(EMAIL_REGEX), trim(col("email"))
    ).otherwise(None)

    df_cleaned = df_raw.select(
        trim(col("client_nk")).alias("client_nk"),
        trim(col("prenom")).alias("prenom"),
        trim(col("nom")).alias("nom"),
        email_clean.alias("email"),
        trim(col("telephone")).alias("telephone"),
        trim(col("ville")).alias("ville"),
        to_date(trim(col("date_naissance"))).alias("date_naissance"),
        to_date(trim(col("date_inscription"))).alias("date_inscription"),
        trim(col("segment")).alias("segment")
    )

    invalid_cond = (
        col("client_nk").isNull() |
        col("prenom").isNull() |
        col("nom").isNull() |
        col("telephone").isNull() |
        col("ville").isNull() |
        col("date_naissance").isNull() |
        col("date_inscription").isNull() |
        col("segment").isNull()
    )
    df_valid, df_rej = split_rejected(df_cleaned, invalid_cond, "dim_client", "Champ obligatoire NULL ou date invalide")
    num_rej = write_rejected(df_rej)

    df_dedup = df_valid.dropDuplicates(["client_nk"])
    df_dedup.write.jdbc(url=JDBC_URL, table="silver.dim_client", mode="append", properties=JDBC_PROPS)
    print(f"   [OK] silver.dim_client : {df_dedup.count()} lignes inserees ({num_rej} rejets)")
    return df_dedup


def clean_dim_temps(spark: SparkSession) -> DataFrame:
    """Nettoie bronze.dim_temps -> silver.dim_temps."""
    print("\n>> Nettoyage de bronze.dim_temps...")
    df_raw = spark.read.jdbc(url=JDBC_URL, table="bronze.dim_temps", properties=JDBC_PROPS)

    df_cleaned = df_raw.select(
        col("temps_sk").cast("int").alias("temps_sk"),
        to_date(trim(col("date_complete"))).alias("date_complete"),
        col("jour").cast("int").alias("jour"),
        col("jour_semaine_num").cast("int").alias("jour_semaine_num"),
        trim(col("jour_semaine_nom")).alias("jour_semaine_nom"),
        col("semaine_annee").cast("int").alias("semaine_annee"),
        col("mois_num").cast("int").alias("mois_num"),
        trim(col("mois_nom")).alias("mois_nom"),
        col("trimestre").cast("int").alias("trimestre"),
        col("semestre").cast("int").alias("semestre"),
        col("annee").cast("int").alias("annee"),
        col("est_weekend").cast("boolean").alias("est_weekend"),
        col("est_ferie").cast("boolean").alias("est_ferie"),
        col("est_jour_ouvre").cast("boolean").alias("est_jour_ouvre")
    )

    invalid_cond = col("temps_sk").isNull() | col("date_complete").isNull()
    df_valid, df_rej = split_rejected(df_cleaned, invalid_cond, "dim_temps", "temps_sk ou date_complete NULL")
    num_rej = write_rejected(df_rej)

    df_dedup = df_valid.dropDuplicates(["temps_sk"])
    df_dedup.write.jdbc(url=JDBC_URL, table="silver.dim_temps", mode="append", properties=JDBC_PROPS)
    print(f"   [OK] silver.dim_temps : {df_dedup.count()} lignes inserees ({num_rej} rejets)")
    return df_dedup


def run_clean_dimensions(spark: SparkSession) -> dict[str, DataFrame]:
    """Exécute le nettoyage complet des 5 dimensions dans l'ordre de leurs dépendances."""
    print("=" * 70)
    print("  RetailPlus — Silver Layer : Nettoyage des Dimensions")
    print("=" * 70)

    t0 = time.time()
    df_magasin     = clean_dim_magasin(spark)
    df_fournisseur = clean_dim_fournisseur(spark)
    df_produit     = clean_dim_produit(spark, df_fournisseur)
    df_client      = clean_dim_client(spark)
    df_temps       = clean_dim_temps(spark)

    print(f"\n[DONE] Nettoyage des dimensions termine en {time.time() - t0:.1f}s")
    return {
        "dim_magasin": df_magasin,
        "dim_fournisseur": df_fournisseur,
        "dim_produit": df_produit,
        "dim_client": df_client,
        "dim_temps": df_temps,
    }


if __name__ == "__main__":
    spark = get_spark_session("RetailPlus-Silver-Dimensions", packages=["org.postgresql:postgresql:42.7.3"])
    run_clean_dimensions(spark)
    spark.stop()
