# =============================================================================
# RetailPlus — spark_jobs/utils/spark_session.py
# Factory réutilisable pour créer une SparkSession configurée avec les
# packages JDBC PostgreSQL et Spark-Kafka.
# =============================================================================

import sys
import os

# Permet l'import de config depuis n'importe quel point d'exécution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import SparkSession
from config import SPARK_PACKAGES


def get_spark_session(app_name: str = "RetailPlus", packages: list[str] = None) -> SparkSession:
    """
    Crée et retourne une SparkSession configurée pour le projet RetailPlus.

    Args:
        app_name: Nom de l'application Spark.
        packages: Liste optionnelle de packages Maven à charger.
                  Si non renseignée, utilise SPARK_PACKAGES.
    """
    if packages is None:
        packages_str = ",".join(SPARK_PACKAGES)
    else:
        packages_str = ",".join(packages)

    builder = (
        SparkSession.builder
        .appName(app_name)
        # Force la résolution sur le dépôt central Maven
        .config("spark.jars.repositories", "https://repo1.maven.org/maven2")
        .config("spark.jars.packages", packages_str)
        # Configuration mémoire pour les gros CSV (fait_ventes ~560 Mo)
        .config("spark.driver.memory", "4g")
        .config("spark.executor.memory", "2g")
        # Encodage UTF-8 systématique
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.sources.partitionOverwriteMode", "dynamic")
        # Performance
        .config("spark.sql.shuffle.partitions", "8")
    )

    spark = builder.getOrCreate()

    # Réduction du verbosité des logs Spark pour garder la console lisible
    spark.sparkContext.setLogLevel("WARN")

    return spark
