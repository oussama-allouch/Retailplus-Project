# =============================================================================
# RetailPlus — spark_jobs/streaming/ingest_kafka_ventes.py
# Pipeline Streaming : consomme les topics Kafka retailplus.ventes et
# retailplus.retours en PySpark Structured Streaming, puis écrit dans
# les tables bronze.fait_ventes et bronze.fait_retours de PostgreSQL.
#
# Le producteur Kafka (data_generator/kafka_producer/producer.py) envoie
# des événements JSON avec un champ « event_type » = "VENTE" ou "RETOUR".
#
# Usage :
#     python spark_jobs/streaming/ingest_kafka_ventes.py
#     # ou via spark-submit :
#     spark-submit --packages org.postgresql:postgresql:42.7.3,\
#                             org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.9 \
#                  spark_jobs/streaming/ingest_kafka_ventes.py
# =============================================================================

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import DataFrame
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, DoubleType,
    ArrayType,
)
from pyspark.sql.functions import (
    from_json, col, explode, current_timestamp, lit,
)

from config import JDBC_URL, JDBC_PROPS, KAFKA_BOOTSTRAP, KAFKA_TOPICS
from utils.spark_session import get_spark_session


# ─── Schémas JSON des événements Kafka ────────────────────────────────────────
# Ces schémas doivent correspondre exactement à la structure des événements
# produits par data_generator/kafka_producer/producer.py

LIGNE_VENTE_SCHEMA = StructType([
    StructField("produit_nk",    StringType(),  True),
    StructField("quantite",      IntegerType(), True),
    StructField("prix_unitaire", DoubleType(),  True),
    StructField("montant_ttc",   DoubleType(),  True),
])

VENTE_EVENT_SCHEMA = StructType([
    StructField("event_id",          StringType(),  True),
    StructField("event_type",        StringType(),  True),
    StructField("timestamp",         StringType(),  True),
    StructField("ticket_nk",         StringType(),  True),
    StructField("magasin_nk",        StringType(),  True),
    StructField("client_nk",         StringType(),  True),
    StructField("lignes",            ArrayType(LIGNE_VENTE_SCHEMA), True),
    StructField("montant_total_ttc", DoubleType(),  True),
    StructField("source",            StringType(),  True),
])

RETOUR_EVENT_SCHEMA = StructType([
    StructField("event_id",    StringType(),  True),
    StructField("event_type",  StringType(),  True),
    StructField("timestamp",   StringType(),  True),
    StructField("retour_nk",   StringType(),  True),
    StructField("magasin_nk",  StringType(),  True),
    StructField("produit_nk",  StringType(),  True),
    StructField("quantite",    IntegerType(), True),
    StructField("montant_ttc", DoubleType(),  True),
    StructField("motif",       StringType(),  True),
    StructField("source",      StringType(),  True),
])


# ─── Fonctions de transformation ─────────────────────────────────────────────

def _transform_ventes_batch(df: DataFrame) -> DataFrame:
    """
    Transforme un micro-batch d'événements de vente Kafka en lignes
    compatibles avec la table bronze.fait_ventes.

    Chaque événement contient un tableau « lignes » qui est « explodé »
    en lignes individuelles (une ligne par produit vendu dans le ticket).
    """
    df_parsed = df.select(
        from_json(col("value").cast("string"), VENTE_EVENT_SCHEMA).alias("event")
    ).select("event.*")

    # Explosion : 1 événement → N lignes (une par produit dans le ticket)
    df_exploded = df_parsed.select(
        col("ticket_nk"),
        col("timestamp").alias("timestamp_vente"),
        lit(None).cast("string").alias("date_vente"),       # sera calculé en Silver
        col("magasin_nk"),
        col("client_nk"),
        explode(col("lignes")).alias("ligne"),
    )

    # Extraction des champs de la ligne
    df_flat = df_exploded.select(
        col("ticket_nk"),
        col("timestamp_vente"),
        col("date_vente"),
        col("magasin_nk"),
        col("client_nk"),
        col("ligne.produit_nk").alias("produit_nk"),
        col("ligne.quantite").cast("string").alias("quantite"),
        col("ligne.prix_unitaire").cast("string").alias("prix_unitaire_ht"),
        lit(None).cast("string").alias("tva_pct"),
        col("ligne.prix_unitaire").cast("string").alias("prix_unitaire_ttc"),
        lit(None).cast("string").alias("montant_ht"),
        col("ligne.montant_ttc").cast("string").alias("montant_ttc"),
        lit(None).cast("string").alias("marge_brute_unit"),
        lit(None).cast("string").alias("marge_brute_total"),
    )

    return df_flat


def _transform_retours_batch(df: DataFrame) -> DataFrame:
    """
    Transforme un micro-batch d'événements de retour Kafka en lignes
    compatibles avec la table bronze.fait_retours.
    """
    df_parsed = df.select(
        from_json(col("value").cast("string"), RETOUR_EVENT_SCHEMA).alias("event")
    ).select("event.*")

    df_flat = df_parsed.select(
        col("retour_nk"),
        lit(None).cast("string").alias("ticket_nk"),
        col("produit_nk"),
        col("magasin_nk"),
        lit(None).cast("string").alias("client_nk"),
        lit(None).cast("string").alias("date_vente_originale"),
        col("timestamp").alias("date_retour"),
        col("quantite").cast("string").alias("quantite_retournee"),
        col("montant_ttc").cast("string").alias("montant_rembourse"),
        col("motif"),
    )

    return df_flat


# ─── Fonctions foreachBatch (sink JDBC) ───────────────────────────────────────

def _write_ventes_batch(batch_df: DataFrame, batch_id: int) -> None:
    """Callback foreachBatch : écrit un micro-batch de ventes dans PostgreSQL."""
    if batch_df.isEmpty():
        return
    count = batch_df.count()
    batch_df.write.jdbc(
        url=JDBC_URL,
        table="bronze.fait_ventes",
        mode="append",
        properties=JDBC_PROPS,
    )
    print(f"   [WRITE] Batch #{batch_id} - {count} ventes inserees dans bronze.fait_ventes")


def _write_retours_batch(batch_df: DataFrame, batch_id: int) -> None:
    """Callback foreachBatch : écrit un micro-batch de retours dans PostgreSQL."""
    if batch_df.isEmpty():
        return
    count = batch_df.count()
    batch_df.write.jdbc(
        url=JDBC_URL,
        table="bronze.fait_retours",
        mode="append",
        properties=JDBC_PROPS,
    )
    print(f"   [WRITE] Batch #{batch_id} - {count} retours inseres dans bronze.fait_retours")


# ─── Point d'entrée principal ─────────────────────────────────────────────────

def main() -> None:
    """Lance les deux streams Kafka → PostgreSQL en parallèle."""
    print("=" * 70)
    print("  RetailPlus - Ingestion Streaming Kafka -> Bronze PostgreSQL")
    print(f"  Kafka : {KAFKA_BOOTSTRAP}")
    print(f"  Topics : {KAFKA_TOPICS['ventes']}, {KAFKA_TOPICS['retours']}")
    print("=" * 70)

    spark = get_spark_session("RetailPlus-Streaming-Bronze")

    # ─── Stream 1 : Ventes ────────────────────────────────────────────────
    print("\n>> Demarrage du stream VENTES...")
    df_kafka_ventes = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
        .option("subscribe", KAFKA_TOPICS["ventes"])
        .option("startingOffsets", "earliest")
        .option("failOnDataLoss", "false")
        .load()
    )

    query_ventes = (
        df_kafka_ventes
        .transform(_transform_ventes_batch)
        .writeStream
        .outputMode("append")
        .foreachBatch(_write_ventes_batch)
        .option("checkpointLocation", "/tmp/retailplus/checkpoints/ventes")
        .trigger(processingTime="10 seconds")
        .queryName("stream_ventes_to_bronze")
        .start()
    )

    # ─── Stream 2 : Retours ───────────────────────────────────────────────
    print(">> Demarrage du stream RETOURS...")
    df_kafka_retours = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
        .option("subscribe", KAFKA_TOPICS["retours"])
        .option("startingOffsets", "earliest")
        .option("failOnDataLoss", "false")
        .load()
    )

    query_retours = (
        df_kafka_retours
        .transform(_transform_retours_batch)
        .writeStream
        .outputMode("append")
        .foreachBatch(_write_retours_batch)
        .option("checkpointLocation", "/tmp/retailplus/checkpoints/retours")
        .trigger(processingTime="10 seconds")
        .queryName("stream_retours_to_bronze")
        .start()
    )

    print("\n[OK] Streams actifs. En attente d'evenements Kafka... (Ctrl+C pour arreter)")
    spark.streams.awaitAnyTermination()


if __name__ == "__main__":
    main()
