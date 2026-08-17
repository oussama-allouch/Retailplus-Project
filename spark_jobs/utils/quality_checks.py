# =============================================================================
# RetailPlus — spark_jobs/utils/quality_checks.py
# Utilitaires de validation de données et de gestion des rejets (Silver Layer)
# =============================================================================

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, to_json, struct, current_timestamp
from config import JDBC_URL, JDBC_PROPS


def split_rejected(df: DataFrame, invalid_condition, table_name: str, reason: str) -> tuple[DataFrame, DataFrame]:
    """
    Sépare un DataFrame en deux : (df_valid, df_rejected).
    
    Args:
        df: DataFrame source.
        invalid_condition: Condition PySpark (Column) identifiant les lignes INVALIDES.
        table_name: Nom de la table source pour la gouvernance dans silver.rejected_records.
        reason: Raison du rejet.

    Returns:
        tuple (df_valid, df_rejected_formatted)
        df_rejected_formatted est au format exact de silver.rejected_records:
        - table_name (string)
        - record_data (string / JSON)
        - reason (string)
    """
    df_invalid = df.filter(invalid_condition)
    df_valid   = df.filter(~(invalid_condition))

    # Formater les rejets sous forme de JSON structuré pour silver.rejected_records
    df_rejected_formatted = df_invalid.select(
        col("table_name") if "table_name" in df_invalid.columns else col("*")
    )
    
    # Transformation des colonnes d'origine en un objet JSON unique
    df_rejected_formatted = df_invalid.select(
        to_json(struct("*")).alias("record_data")
    ).withColumn(
        "table_name", to_json(struct("*")).expr if False else col("record_data") # dummy line for column addition
    )
    
    # On reconstruit proprement le DataFrame de rejets
    df_rejected_formatted = df_invalid.select(
        to_json(struct("*")).alias("record_data")
    ).selectExpr(
        f"'{table_name}' as table_name",
        "record_data",
        f"'{reason}' as reason"
    )

    return df_valid, df_rejected_formatted


def filter_referential_integrity(
    df: DataFrame,
    ref_df: DataFrame,
    fk_col: str,
    pk_col: str,
    table_name: str,
    reason: str,
    allow_null_fk: bool = False
) -> tuple[DataFrame, DataFrame]:
    """
    Vérifie l'intégrité référentielle entre df (table de faits/child) et ref_df (dimension/parent).

    Args:
        df: DataFrame enfant (ex: fait_ventes).
        ref_df: DataFrame parent (ex: dim_client).
        fk_col: Colonne clé étrangère dans df.
        pk_col: Colonne clé primaire dans ref_df.
        table_name: Nom de la table pour les rejets.
        reason: Motif du rejet en cas d'absence.
        allow_null_fk: Si True, une FK NULL est considérée valide.

    Returns:
        tuple (df_valid, df_rejected_formatted)
    """
    # Sélectionner les clés primaires distictes existantes
    valid_keys = ref_df.select(col(pk_col).alias("_ref_pk")).distinct()

    # Left join pour repérer les orphelins
    joined = df.join(valid_keys, df[fk_col] == valid_keys["_ref_pk"], "left")

    if allow_null_fk:
        # Rejet uniquement si fk_col est NON-NULL et _ref_pk est NULL
        invalid_cond = col(fk_col).isNotNull() & col("_ref_pk").isNull()
    else:
        # Rejet si fk_col est NULL ou si _ref_pk est NULL
        invalid_cond = col(fk_col).isNull() | col("_ref_pk").isNull()

    df_invalid = joined.filter(invalid_cond).drop("_ref_pk")
    df_valid   = joined.filter(~invalid_cond).drop("_ref_pk")

    # Formater les rejets
    df_rejected_formatted = df_invalid.select(
        to_json(struct("*")).alias("record_data")
    ).selectExpr(
        f"'{table_name}' as table_name",
        "record_data",
        f"'{reason}' as reason"
    )

    return df_valid, df_rejected_formatted


def write_rejected(df_rejected: DataFrame) -> int:
    """
    Écrit un DataFrame de rejets dans la table silver.rejected_records via JDBC.

    Returns:
        Nombre de lignes de rejets insérées.
    """
    count = df_rejected.count()
    if count > 0:
        df_rejected.write.jdbc(
            url=JDBC_URL,
            table="silver.rejected_records",
            mode="append",
            properties=JDBC_PROPS
        )
    return count
