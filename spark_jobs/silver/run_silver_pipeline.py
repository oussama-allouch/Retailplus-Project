# =============================================================================
# RetailPlus — spark_jobs/silver/run_silver_pipeline.py
# Point d'entrée principal pour exécuter l'ensemble du pipeline Silver
# (Bronze -> Silver : Nettoyage, Déduplication, Typage, Rejets)
# =============================================================================

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import JDBC_URL, JDBC_PROPS
from utils.spark_session import get_spark_session
from silver.clean_dimensions import run_clean_dimensions
from silver.clean_transactions import run_clean_transactions


def print_summary(spark) -> None:
    """Affiche un résumé comparatif des volumes Bronze vs Silver et du nombre de rejets."""
    print("\n" + "=" * 70)
    print("  RAPPORT FINAL — PIPELINE SILVER")
    print("=" * 70)

    tables = [
        "dim_magasin", "dim_fournisseur", "dim_produit", "dim_client", "dim_temps",
        "fait_stock", "fait_commandes", "fait_lignes_commandes", "fait_ventes", "fait_retours"
    ]

    print(f"{'Table':<25} | {'Bronze':>12} | {'Silver':>12} | {'Éliminés / Rejetés':>20}")
    print("-" * 75)

    total_bronze = 0
    total_silver = 0

    for tbl in tables:
        b_count = spark.read.jdbc(url=JDBC_URL, table=f"bronze.{tbl}", properties=JDBC_PROPS).count()
        s_count = spark.read.jdbc(url=JDBC_URL, table=f"silver.{tbl}", properties=JDBC_PROPS).count()
        diff = b_count - s_count
        total_bronze += b_count
        total_silver += s_count
        print(f"{tbl:<25} | {b_count:>12,} | {s_count:>12,} | {diff:>20,}")

    print("-" * 75)
    print(f"{'TOTAL':<25} | {total_bronze:>12,} | {total_silver:>12,} | {total_bronze - total_silver:>20,}")

    # Résumé de la table silver.rejected_records
    df_rejs = spark.read.jdbc(url=JDBC_URL, table="silver.rejected_records", properties=JDBC_PROPS)
    rej_total = df_rejs.count()

    print(f"\n[REJETS GOVERNANCE] Total d'enregistrements insérés dans silver.rejected_records : {rej_total:,}")
    if rej_total > 0:
        print("\nRépartition des rejets par table et motif :")
        df_rejs.groupBy("table_name", "reason").count().show(50, truncate=False)

    print("=" * 70)


def main() -> None:
    print("=" * 70)
    print("  RetailPlus — Execution du Pipeline Silver Complète (Bronze -> Silver)")
    print("=" * 70)

    t_start = time.time()
    spark = get_spark_session("RetailPlus-Silver-Pipeline", packages=["org.postgresql:postgresql:42.7.3"])

    try:
        # 1. Dimensions
        dims = run_clean_dimensions(spark)

        # 2. Transactions (Faits)
        run_clean_transactions(spark, dims)

        # 3. Rapport final
        print_summary(spark)

        elapsed = time.time() - t_start
        print(f"\n[DONE] Pipeline Silver execute avec succes en {elapsed:.1f}s")

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
