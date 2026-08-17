# =============================================================================
# RetailPlus — airflow/dags/dag_silver_transformation.py
# DAG Airflow : Nettoyage & Transformation Bronze → Couche Silver (PostgreSQL)
#
# Ce DAG exécute le pipeline Silver complet (nettoyage, déduplication,
# typage fort, contrôle qualité et isolation des rejets) via DockerOperator.
#
# Planification : @daily (rafraîchissement quotidien de la couche Silver)
# =============================================================================

from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount

# ─── Constantes ───────────────────────────────────────────────────────────────
WORKSPACE_PATH   = "/opt/spark/workspace"
SPARK_SUBMIT_CMD = "/opt/spark/bin/spark-submit"
PG_PACKAGE       = "org.postgresql:postgresql:42.7.3"
DOCKER_NETWORK   = "retailplus-net"

# ─── Arguments par défaut ─────────────────────────────────────────────────────
default_args = {
    "owner":            "retailplus",
    "retries":          1,
    "retry_delay":      timedelta(minutes=10),
    "email_on_failure": False,
    "email_on_retry":   False,
}

# ─── Définition du DAG ────────────────────────────────────────────────────────
with DAG(
    dag_id="dag_silver_transformation",
    description="Nettoyage & Qualité Bronze → Silver : Déduplication, Typage, Rejets (PySpark via Spark container)",
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["retailplus", "silver", "transformation", "quality"],
    doc_md="""
## DAG : Transformation Silver (Qualité & Nettoyage)

Orchestre le pipeline de transformation et de contrôle qualité de la couche Bronze vers Silver.

### Séquence d'exécution
1. **run_silver_pipeline** → Exécute l'orchestrateur Silver complet :
   - Nettoyage et typage fort de toutes les dimensions
   - Déduplication des transactions (élimination des doublons Kafka)
   - Validation e-mail, contraintes FK, valeurs négatives
   - Redirection des rejets vers `silver.rejected_records`

### Volumes attendus (référence)
- **3 970 815** lignes nettoyées dans `silver`
- **289 236** rejets dans `silver.rejected_records`
- **123 675** doublons éliminés
    """,
) as dag:

    # ── Tâche 1 : Pipeline Silver complet ─────────────────────────────────────
    run_silver_pipeline = DockerOperator(
        task_id="run_silver_pipeline",
        container_name="retailplus-spark-task-silver",
        image="apache/spark:3.5.9",
        command=(
            f"{SPARK_SUBMIT_CMD} "
            f"--packages {PG_PACKAGE} "
            f"--conf spark.ui.enabled=false "
            f"{WORKSPACE_PATH}/spark_jobs/silver/run_silver_pipeline.py"
        ),
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
        # Timeout large car Silver traite ~4M lignes
        execution_timeout=timedelta(hours=2),
    )
