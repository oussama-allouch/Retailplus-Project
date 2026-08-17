# =============================================================================
# RetailPlus — airflow/dags/dag_gold_warehouse.py
# DAG Airflow : Modélisation Dimensionnelle Silver → Couche Gold (Star Schema)
#
# Ce DAG :
# 1. Purge les tables Gold (TRUNCATE CASCADE via BashOperator + psql)
# 2. Reconstruit les dimensions Gold avec Surrogate Keys (_sk)
# 3. Alimente les tables de faits Gold avec résolution des FK dimensionnelles
#
# Planification : @daily (rafraîchissement quotidien du Data Warehouse)
# =============================================================================

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
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

# ─── SQL de purge des tables Gold (ordre inverse des FK) ─────────────────────
TRUNCATE_GOLD_SQL = """
    TRUNCATE TABLE gold.fait_retours          CASCADE;
    TRUNCATE TABLE gold.fait_ventes           CASCADE;
    TRUNCATE TABLE gold.fait_lignes_commandes CASCADE;
    TRUNCATE TABLE gold.fait_commandes        CASCADE;
    TRUNCATE TABLE gold.fait_stock            CASCADE;
    TRUNCATE TABLE gold.dim_temps             CASCADE;
    TRUNCATE TABLE gold.dim_client            CASCADE;
    TRUNCATE TABLE gold.dim_produit           CASCADE;
    TRUNCATE TABLE gold.dim_fournisseur       CASCADE;
    TRUNCATE TABLE gold.dim_magasin           CASCADE;
"""

# ─── Définition du DAG ────────────────────────────────────────────────────────
with DAG(
    dag_id="dag_gold_warehouse",
    description="Modélisation Dimensionnelle Silver → Gold Star Schema (PySpark via Spark container)",
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["retailplus", "gold", "dwh", "star-schema"],
    doc_md="""
## DAG : Data Warehouse Gold (Star Schema)

Orchestre la modélisation dimensionnelle et l'alimentation du schéma en étoile Gold.

### Séquence d'exécution
1. **truncate_gold_tables** → Purge propre de toutes les tables Gold (TRUNCATE CASCADE via psql).
2. **run_gold_pipeline** → Exécute l'orchestrateur Gold complet :
   - Génération des Surrogate Keys (SK) pour les 5 dimensions
   - Dimension temps étendue 2024-2030 (2 557 jours) avec Spark SQL `sequence()`
   - Résolution des FK dimensionnelles sur les 4 tables de faits
   - Rapport comparatif Silver vs Gold

### Volumes attendus (référence)
| Table | Lignes |
|---|---|
| dim_magasin | 5 |
| dim_fournisseur | 8 |
| dim_produit | 500 |
| dim_client | 10 000 |
| dim_temps | 2 557 |
| fait_stock | 30 000 |
| fait_commandes | 2 000 |
| fait_lignes_commandes | 15 811 |
| fait_ventes | 3 831 984 |
| fait_retours | 80 141 |
    """,
) as dag:

    # ── Tâche 1 : Purge des tables Gold ───────────────────────────────────────
    truncate_gold_tables = BashOperator(
        task_id="truncate_gold_tables",
        bash_command=(
            "docker exec retailplus-postgres-dwh "
            "psql -U retailuser -d retailplus -c "
            f'"{TRUNCATE_GOLD_SQL.strip()}"'
        ),
    )

    # ── Tâche 2 : Pipeline Gold complet ───────────────────────────────────────
    run_gold_pipeline = DockerOperator(
        task_id="run_gold_pipeline",
        container_name="retailplus-spark-task-gold",
        image="apache/spark:3.5.9",
        command=(
            f"{SPARK_SUBMIT_CMD} "
            f"--packages {PG_PACKAGE} "
            f"--conf spark.ui.enabled=false "
            f"{WORKSPACE_PATH}/spark_jobs/gold/run_gold_pipeline.py"
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
        # Timeout large car le pipeline Gold traite ~4M lignes (fait_ventes)
        execution_timeout=timedelta(hours=3),
    )

    # ── Dépendances : purger avant de re-remplir ──────────────────────────────
    truncate_gold_tables >> run_gold_pipeline
