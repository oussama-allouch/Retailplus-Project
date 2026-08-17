# =============================================================================
# RetailPlus — spark_jobs/batch/ingest_referentiels.py
# Pipeline Batch : Ingestion des 5 dimensions CSV → schéma bronze PostgreSQL.
#
# Usage :
#     python spark_jobs/batch/ingest_referentiels.py
#     # ou via spark-submit :
#     spark-submit --packages org.postgresql:postgresql:42.7.3 \
#                  spark_jobs/batch/ingest_referentiels.py
# =============================================================================

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import DataFrame
from pyspark.sql.functions import current_timestamp, lit

from config import CSV_DIR, JDBC_URL, JDBC_PROPS, REFERENTIELS_MAPPING
from utils.spark_session import get_spark_session


# ─── Constantes ───────────────────────────────────────────────────────────────
BATCH_MODE = "append"   # append car la table bronze est un « landing zone » brut


def _load_csv(spark, csv_name: str) -> DataFrame:
    """Charge un fichier CSV avec inférence de schéma et détection d'en-têtes."""
    path = os.path.join(CSV_DIR, f"{csv_name}.csv")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"❌ Fichier introuvable : {path}")

    df = (
        spark.read
        .option("header", "true")
        .option("inferSchema", "true")
        .option("encoding", "UTF-8")
        .csv(path)
    )
    return df


def _select_bronze_columns(df: DataFrame, columns: list[str]) -> DataFrame:
    """
    Sélectionne uniquement les colonnes attendues par le schéma bronze.
    Convertit toutes les valeurs en String (le schéma bronze utilise VARCHAR partout
    pour accepter les données brutes sans rejet).
    """
    # Vérification que toutes les colonnes requises existent dans le DataFrame
    missing = set(columns) - set(df.columns)
    if missing:
        raise ValueError(f"❌ Colonnes manquantes dans le CSV : {missing}")

    # Sélection + cast en string (le bronze est tout en VARCHAR)
    df_selected = df.select(*columns)
    for col_name in columns:
        df_selected = df_selected.withColumn(col_name, df_selected[col_name].cast("string"))

    return df_selected


def _write_to_postgres(df: DataFrame, table_name: str) -> int:
    """Écrit un DataFrame dans PostgreSQL via JDBC."""
    row_count = df.count()
    df.write.jdbc(
        url=JDBC_URL,
        table=table_name,
        mode=BATCH_MODE,
        properties=JDBC_PROPS,
    )
    return row_count


def main() -> None:
    """Point d'entrée principal : ingestion des 5 référentiels."""
    print("=" * 70)
    print("  RetailPlus — Ingestion Batch des Référentiels (Dimensions)")
    print("  Cible : PostgreSQL -> schema bronze")
    print("=" * 70)

    spark = get_spark_session("RetailPlus-Batch-Referentiels", packages=["org.postgresql:postgresql:42.7.3"])
    total_rows = 0
    t_start = time.time()

    for csv_name, (table_name, columns) in REFERENTIELS_MAPPING.items():
        t0 = time.time()
        print(f"\n>> Traitement de {csv_name}.csv -> {table_name}")

        # 1. Chargement du CSV
        df_raw = _load_csv(spark, csv_name)
        print(f"   [OK] CSV charge : {df_raw.count()} lignes, {len(df_raw.columns)} colonnes")

        # 2. Sélection et cast des colonnes bronze
        df_bronze = _select_bronze_columns(df_raw, columns)

        # 3. Écriture dans PostgreSQL
        row_count = _write_to_postgres(df_bronze, table_name)
        elapsed = time.time() - t0
        total_rows += row_count

        print(f"   [OK] {row_count:,} lignes inserees dans {table_name} ({elapsed:.1f}s)")

    elapsed_total = time.time() - t_start
    print(f"\n{'=' * 70}")
    print(f"  [DONE] Ingestion terminee : {total_rows:,} lignes au total ({elapsed_total:.1f}s)")
    print(f"{'=' * 70}")

    spark.stop()


if __name__ == "__main__":
    main()
