# =============================================================================
# RetailPlus — airflow/dags/dag_bronze_ingestion.py
# DAG Airflow : Ingestion Batch CSV → schéma Bronze (PostgreSQL)
#
# Ce DAG exécute les deux jobs PySpark d'ingestion batch en lançant
# spark-submit directement dans le conteneur Spark via DockerOperator.
#
# Planification : @once (données historiques) — déclenchable manuellement.
# =============================================================================

from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount

# ─── Constantes ───────────────────────────────────────────────────────────────
SPARK_CONTAINER  = "retailplus-spark-master"
WORKSPACE_PATH   = "/opt/spark/workspace"
SPARK_SUBMIT_CMD = "/opt/spark/bin/spark-submit"
PG_PACKAGE       = "org.postgresql:postgresql:42.7.3"
DOCKER_NETWORK   = "retailplus-net"

# ─── Arguments par défaut ─────────────────────────────────────────────────────
default_args = {
    "owner":            "retailplus",
    "retries":          1,
    "retry_delay":      timedelta(minutes=5),
    "email_on_failure": False,
    "email_on_retry":   False,
}


def make_spark_command(script_relative_path: str) -> str:
    """Construit la commande spark-submit pour un script PySpark donné."""
    return (
        f"{SPARK_SUBMIT_CMD} "
        f"--packages {PG_PACKAGE} "
        f"--conf spark.ui.enabled=false "
        f"{WORKSPACE_PATH}/{script_relative_path}"
    )


# ─── Définition du DAG ────────────────────────────────────────────────────────
with DAG(
    dag_id="dag_bronze_ingestion",
    description="Ingestion Batch CSV → Bronze : Dimensions + Transactions (PySpark via Spark container)",
    schedule_interval="@once",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["retailplus", "bronze", "batch", "ingestion"],
    doc_md="""
## DAG : Ingestion Bronze (Batch)

Charge les données historiques CSV vers le schéma `bronze` de PostgreSQL.

### Séquence d'exécution
1. **ingest_referentiels** → Charge les 5 dimensions (magasins, fournisseurs, produits, clients, temps) - ~11k lignes.
2. **ingest_transactions** → Charge les 5 tables de faits historiques - ~4.38M lignes (fait_ventes ~4.2M).

### Déclenchement
- `@once` pour l'ingestion initiale.
- Déclenchable manuellement depuis l'interface Airflow.
    """,
) as dag:

    # ── Tâche 1 : Ingestion des référentiels (dimensions) ──────────────────────
    ingest_referentiels = DockerOperator(
        task_id="ingest_referentiels",
        container_name="retailplus-spark-task-ingest-refs",
        image="apache/spark:3.5.9",
        command=make_spark_command("spark_jobs/batch/ingest_referentiels.py"),
        docker_url="unix://var/run/docker.sock",
        network_mode=DOCKER_NETWORK,
        mounts=[
            Mount(
                source=WORKSPACE_PATH,
                target=WORKSPACE_PATH,
                type="bind",
            )
        ],
        environment={
            "POSTGRES_HOST": "retailplus-postgres-dwh",
            "POSTGRES_PORT": "5432",
        },
        auto_remove="force",
        mount_tmp_dir=False,
        tty=False,
    )

    # ── Tâche 2 : Ingestion des transactions (faits) ───────────────────────────
    ingest_transactions = DockerOperator(
        task_id="ingest_transactions",
        container_name="retailplus-spark-task-ingest-txns",
        image="apache/spark:3.5.9",
        command=make_spark_command("spark_jobs/batch/ingest_transactions.py"),
        docker_url="unix://var/run/docker.sock",
        network_mode=DOCKER_NETWORK,
        mounts=[
            Mount(
                source=WORKSPACE_PATH,
                target=WORKSPACE_PATH,
                type="bind",
            )
        ],
        environment={
            "POSTGRES_HOST": "retailplus-postgres-dwh",
            "POSTGRES_PORT": "5432",
        },
        auto_remove="force",
        mount_tmp_dir=False,
        tty=False,
    )

    # ── Dépendances : référentiels en premier (FK dans les faits) ─────────────
    ingest_referentiels >> ingest_transactions
