# =============================================================================
# RetailPlus — spark_jobs/batch/ingest_transactions.py
# Pipeline Batch : Ingestion des 5 tables de faits CSV → schéma bronze PostgreSQL.
#
# Ce script traite les tables transactionnelles volumineuses.
# fait_ventes (~4.2M lignes, ~560 Mo) est partitionné automatiquement par Spark.
#
# Usage :
#     python spark_jobs/batch/ingest_transactions.py
#     # ou via spark-submit :
#     spark-submit --packages org.postgresql:postgresql:42.7.3 \
#                  spark_jobs/batch/ingest_transactions.py
# =============================================================================

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import DataFrame
from pyspark.sql.functions import current_timestamp

from config import CSV_DIR, JDBC_URL, JDBC_PROPS, TRANSACTIONS_MAPPING
from utils.spark_session import get_spark_session


# ─── Constantes ───────────────────────────────────────────────────────────────
BATCH_MODE   = "append"
# Nombre de partitions JDBC pour l'écriture parallèle des gros DataFrames
JDBC_NUM_PARTITIONS = 8
# Seuil (en lignes) au-delà duquel on active l'écriture partitionnée
LARGE_TABLE_THRESHOLD = 100_000


def _load_csv(spark, csv_name: str) -> DataFrame:
    """Charge un fichier CSV avec inférence de schéma et détection d'en-têtes."""
    path = os.path.join(CSV_DIR, f"{csv_name}.csv")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"[ERROR] Fichier introuvable : {path}")

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
    Sélectionne et convertit en VARCHAR les colonnes attendues par le schéma bronze.
    """
    missing = set(columns) - set(df.columns)
    if missing:
        raise ValueError(f"[ERROR] Colonnes manquantes dans le CSV : {missing}")

    df_selected = df.select(*columns)
    for col_name in columns:
        df_selected = df_selected.withColumn(col_name, df_selected[col_name].cast("string"))

    return df_selected


def _write_to_postgres(df: DataFrame, table_name: str, is_large: bool = False) -> int:
    """
    Écrit un DataFrame dans PostgreSQL via JDBC.
    Pour les tables volumineuses (>100K lignes), repartitionne le DataFrame
    avant l'écriture pour paralléliser les INSERT et éviter les OOM.
    """
    row_count = df.count()

    if is_large:
        print(f"   [INFO] Table volumineuse detectee - repartitionnement en {JDBC_NUM_PARTITIONS} partitions")
        df = df.repartition(JDBC_NUM_PARTITIONS)

    # Configuration JDBC pour l'écriture en batch
    write_props = dict(JDBC_PROPS)
    write_props["batchsize"]         = "10000"
    write_props["reWriteBatchedInserts"] = "true"

    df.write.jdbc(
        url=JDBC_URL,
        table=table_name,
        mode=BATCH_MODE,
        properties=write_props,
    )
    return row_count


def main() -> None:
    """Point d'entrée principal : ingestion des 5 tables de faits."""
    print("=" * 70)
    print("  RetailPlus — Ingestion Batch des Transactions (Faits)")
    print("  Cible : PostgreSQL -> schema bronze")
    print("=" * 70)

    spark = get_spark_session("RetailPlus-Batch-Transactions", packages=["org.postgresql:postgresql:42.7.3"])
    total_rows = 0
    t_start = time.time()

    for csv_name, (table_name, columns) in TRANSACTIONS_MAPPING.items():
        t0 = time.time()
        print(f"\n>> Traitement de {csv_name}.csv -> {table_name}")

        # 1. Chargement du CSV
        df_raw = _load_csv(spark, csv_name)
        raw_count = df_raw.count()
        print(f"   [OK] CSV charge : {raw_count:,} lignes, {len(df_raw.columns)} colonnes")

        # 2. Sélection et cast des colonnes bronze
        df_bronze = _select_bronze_columns(df_raw, columns)

        # 3. Écriture dans PostgreSQL (mode partitionné si volumineuse)
        is_large = raw_count > LARGE_TABLE_THRESHOLD
        row_count = _write_to_postgres(df_bronze, table_name, is_large=is_large)
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
