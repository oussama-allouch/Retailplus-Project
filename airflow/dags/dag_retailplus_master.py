# =============================================================================
# RetailPlus — airflow/dags/dag_retailplus_master.py
# DAG Airflow : Orchestrateur E2E Master — Pipeline Data Platform Complet
#
# Ce DAG maître déclenche séquentiellement les 3 DAGs spécialisés :
#   Bronze (Ingestion) → Silver (Transformation) → Gold (Data Warehouse)
#
# Stratégie : TriggerDagRunOperator pour chaîner les DAGs avec attente de
# complétion (wait_for_completion=True).
#
# Planification : @daily (exécution quotidienne complète du pipeline E2E)
# =============================================================================

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.trigger_rule import TriggerRule

# ─── Arguments par défaut ─────────────────────────────────────────────────────
default_args = {
    "owner":            "retailplus",
    "retries":          0,
    "email_on_failure": False,
    "email_on_retry":   False,
}

# ─── Définition du DAG Master ─────────────────────────────────────────────────
with DAG(
    dag_id="dag_retailplus_master",
    description="Orchestrateur E2E RetailPlus : Bronze → Silver → Gold (Pipeline Data Platform complet)",
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["retailplus", "master", "e2e", "orchestration"],
    doc_md="""
## DAG Master : Pipeline Data Platform RetailPlus (E2E)

Orchestre l'intégralité du pipeline de données en déclenchant séquentiellement les 3 DAGs spécialisés.

### Flux d'exécution
```
start → [Bronze] → [Silver] → [Gold] → end
```

### DAGs déclenchés
| Ordre | DAG | Rôle | Durée estimée |
|---|---|---|---|
| 1 | `dag_bronze_ingestion` | Ingestion CSV → Bronze | ~30 min |
| 2 | `dag_silver_transformation` | Nettoyage Bronze → Silver | ~60 min |
| 3 | `dag_gold_warehouse` | Modélisation Silver → Gold | ~15 min |

### Déclenchement Manuel
Depuis l'interface Airflow (`http://localhost:8081`) → DAG `dag_retailplus_master` → ▶ Trigger DAG.

> **Note** : Le DAG Bronze est planifié `@once` (données historiques). En production,
> seuls les DAGs Silver et Gold seraient exécutés quotidiennement sur les nouvelles données.
    """,
) as dag:

    # ── Point de départ ───────────────────────────────────────────────────────
    start = EmptyOperator(task_id="start")

    # ── Étape 1 : Déclencher le DAG d'ingestion Bronze ────────────────────────
    trigger_bronze = TriggerDagRunOperator(
        task_id="trigger_bronze_ingestion",
        trigger_dag_id="dag_bronze_ingestion",
        wait_for_completion=True,
        poke_interval=60,       # vérifier toutes les 60 secondes
        allowed_states=["success"],
        failed_states=["failed"],
        reset_dag_run=True,
    )

    # ── Étape 2 : Déclencher le DAG de transformation Silver ──────────────────
    trigger_silver = TriggerDagRunOperator(
        task_id="trigger_silver_transformation",
        trigger_dag_id="dag_silver_transformation",
        wait_for_completion=True,
        poke_interval=60,
        allowed_states=["success"],
        failed_states=["failed"],
        reset_dag_run=True,
    )

    # ── Étape 3 : Déclencher le DAG de modélisation Gold ──────────────────────
    trigger_gold = TriggerDagRunOperator(
        task_id="trigger_gold_warehouse",
        trigger_dag_id="dag_gold_warehouse",
        wait_for_completion=True,
        poke_interval=60,
        allowed_states=["success"],
        failed_states=["failed"],
        reset_dag_run=True,
    )

    # ── Point de fin (s'exécute même si une tâche upstream échoue) ────────────
    end = EmptyOperator(
        task_id="end",
        trigger_rule=TriggerRule.ALL_DONE,
    )

    # ── Chaînage séquentiel E2E ───────────────────────────────────────────────
    start >> trigger_bronze >> trigger_silver >> trigger_gold >> end
