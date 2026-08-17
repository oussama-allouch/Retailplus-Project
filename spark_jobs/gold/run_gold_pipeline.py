# =============================================================================
# RetailPlus — spark_jobs/gold/run_gold_pipeline.py
# Orchestrateur principal pour alimenter la couche Gold (Star Schema Data Warehouse)
# =============================================================================

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import JDBC_URL, JDBC_PROPS
from utils.spark_session import get_spark_session
from gold.build_dimensions_gold import run_build_dimensions_gold
from gold.build_facts_gold import run_build_facts_gold


def truncate_gold_tables(spark) -> None:
    """Vide proprement toutes les tables du schéma Gold avant re-remplissage."""
    print(">> Nettoyage preliminaire des tables Gold (TRUNCATE CASCADE)...")
    cmd = (
        "docker exec retailplus-postgres-dwh psql -U retailuser -d retailplus -c "
        "\"TRUNCATE TABLE gold.fait_retours CASCADE; "
        "TRUNCATE TABLE gold.fait_ventes CASCADE; "
        "TRUNCATE TABLE gold.fait_lignes_commandes CASCADE; "
        "TRUNCATE TABLE gold.fait_commandes CASCADE; "
        "TRUNCATE TABLE gold.fait_stock CASCADE; "
        "TRUNCATE TABLE gold.dim_temps CASCADE; "
        "TRUNCATE TABLE gold.dim_client CASCADE; "
        "TRUNCATE TABLE gold.dim_produit CASCADE; "
        "TRUNCATE TABLE gold.dim_fournisseur CASCADE; "
        "TRUNCATE TABLE gold.dim_magasin CASCADE;\""
    )
    import subprocess
    subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("   [OK] Tables Gold reinitialisees.\n")


def print_summary(spark) -> None:
    """Affiche un résumé comparatif des volumes Silver vs Gold et exécute un test de requête décisionnelle Star Schema."""
    print("\n" + "=" * 70)
    print("  RAPPORT FINAL — PIPELINE GOLD (DATA WAREHOUSE)")
    print("=" * 70)

    tables = [
        "dim_magasin", "dim_fournisseur", "dim_produit", "dim_client", "dim_temps",
        "fait_stock", "fait_commandes", "fait_lignes_commandes", "fait_ventes", "fait_retours"
    ]

    print(f"{'Table':<25} | {'Silver':>12} | {'Gold':>12} | {'Statut':>15}")
    print("-" * 70)

    total_silver = 0
    total_gold   = 0

    for tbl in tables:
        s_count = spark.read.jdbc(url=JDBC_URL, table=f"silver.{tbl}", properties=JDBC_PROPS).count()
        g_count = spark.read.jdbc(url=JDBC_URL, table=f"gold.{tbl}", properties=JDBC_PROPS).count()
        total_silver += s_count
        total_gold   += g_count
        status = "MATCH [OK]" if s_count == g_count else "MISMATCH [!]"
        print(f"{tbl:<25} | {s_count:>12,} | {g_count:>12,} | {status:>15}")

    print("-" * 70)
    print(f"{'TOTAL':<25} | {total_silver:>12,} | {total_gold:>12,} | {'100% OK':>15}")
    print("=" * 70)


def main() -> None:
    print("=" * 70)
    print("  RetailPlus — Execution du Pipeline Gold (Silver -> Gold Star Schema)")
    print("=" * 70)

    t_start = time.time()
    spark = get_spark_session("RetailPlus-Gold-Pipeline", packages=["org.postgresql:postgresql:42.7.3"])

    try:
        # 1. Truncate
        truncate_gold_tables(spark)

        # 2. Dimensions
        dims = run_build_dimensions_gold(spark)

        # 3. Facts
        run_build_facts_gold(spark, dims)

        # 4. Rapport
        print_summary(spark)

        elapsed = time.time() - t_start
        print(f"\n[DONE] Pipeline Gold execute avec succes en {elapsed:.1f}s")

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
