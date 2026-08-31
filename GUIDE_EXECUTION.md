# 🚀 RetailPlus — Guide des Commandes d'Exécution

Ce document récapitule toutes les commandes nécessaires pour démarrer, exécuter, orchestrer et visualiser la plateforme de données **RetailPlus**.

---

## 📑 Sommaire
1. [Prérequis & Installation](#1-prérequis--installation)
2. [Démarrage de l'Infrastructure Docker](#2-démarrage-de-linfrastructure-docker)
3. [Génération des Données & Simulation Streaming](#3-génération-des-données--simulation-streaming)
4. [Exécution des Pipelines PySpark (Manuel)](#4-exécution-des-pipelines-pyspark-manuel)
5. [Orchestration avec Apache Airflow](#5-orchestration-avec-apache-airflow)
6. [Lancement du Dashboard BI Streamlit](#6-lancement-du-dashboard-bi-streamlit)
7. [Commandes Utiles de Vérification & Maintenance](#7-commandes-utiles-de-vérification--maintenance)

---

## 1. Prérequis & Installation

### A. Cloner le Projet
```bash
git clone https://github.com/oussama-allouch/Retailplus-Project.git
cd Retailplus-Project
```

### B. Installer les Dépendances Python (Machine Hôte)
```bash
pip install -r data_generator/requirements.txt
pip install psycopg2-binary streamlit plotly sqlalchemy pyspark==3.5.9
```

---

## 2. Démarrage de l'Infrastructure Docker

Lance l'ensemble des conteneurs : PostgreSQL DWH, Kafka, Zookeeper, Spark (Master + Worker) et Airflow (Webserver, Scheduler, DB).

```bash
# Démarrer tous les services en arrière-plan
docker compose up -d

# Vérifier l'état de santé de tous les conteneurs
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### 🌐 Liens d'Accès aux Interfaces Web :
| Service | URL | Identifiants |
|---|---|---|
| **Airflow Webserver** | [http://localhost:8081](http://localhost:8081) | `admin` / `admin` |
| **Spark Master UI** | [http://localhost:8080](http://localhost:8080) | — |
| **Spark Worker UI** | [http://localhost:8082](http://localhost:8082) | — |
| **PostgreSQL DWH** | `localhost:5434` (DB: `retailplus`) | `retailuser` / `retailpassword` |
| **Streamlit BI** | [http://localhost:8501](http://localhost:8501) | — |

---

## 3. Génération des Données & Simulation Streaming

### A. Générer l'Historique des Données (CSV)
Génère ~4.4 millions de lignes de données historiques (référentiels + transactions).

```bash
python data_generator/main.py
```

### B. Lancer le Simulateur de Caisse Temps Réel (Kafka Streaming)
Produit en continu des tickets de vente et de retours dans les topics Kafka `retailplus.ventes` et `retailplus.retours`.

```bash
# Lancer le simulateur (par défaut : 500 événements avec pause de 0.5s)
python data_generator/run_simulator.py

# Ou avec des paramètres personnalisés :
python data_generator/run_simulator.py --events 2000 --interval 0.2
```

---

## 4. Exécution des Pipelines PySpark (Manuel)

Vous pouvez exécuter les jobs Spark directement depuis la machine hôte :

### A. Couche Bronze (Ingestion)
```bash
# Ingestion des référentiels (dimensions CSV -> bronze)
python spark_jobs/batch/ingest_referentiels.py

# Ingestion des transactions volumineuses (faits CSV -> bronze)
python spark_jobs/batch/ingest_transactions.py

# (Optionnel) Job Streaming Kafka -> Bronze
python spark_jobs/streaming/ingest_kafka_ventes.py
```

### B. Couche Silver (Nettoyage & Contrôle Qualité)
Nettoie, déduplique, valide et redirige les anomalies vers `silver.rejected_records`.

```bash
python spark_jobs/silver/run_silver_pipeline.py
```

### C. Couche Gold (Modélisation Star Schema Data Warehouse)
Génère les Surrogate Keys (`_sk`), résout les jointures dimensionnelles et remplit la couche Gold.

```bash
python spark_jobs/gold/run_gold_pipeline.py
```

---

## 5. Orchestration avec Apache Airflow

### A. Débloquer / Activer les DAGs en CLI
```bash
docker exec retailplus-airflow-webserver airflow dags unpause dag_bronze_ingestion
docker exec retailplus-airflow-webserver airflow dags unpause dag_silver_transformation
docker exec retailplus-airflow-webserver airflow dags unpause dag_gold_warehouse
docker exec retailplus-airflow-webserver airflow dags unpause dag_retailplus_master
```

### B. Déclencher le Pipeline E2E Master
Exécute séquentiellement **Bronze ➔ Silver ➔ Gold** de manière automatisée :

```bash
docker exec retailplus-airflow-webserver airflow dags trigger dag_retailplus_master
```

*Vous pouvez également déclencher les DAGs directement via l'interface graphique sur [http://localhost:8081](http://localhost:8081).*

---

## 6. Lancement du Dashboard BI Streamlit

Lance l'application web interactive d'aide à la décision :

```bash
streamlit run dashboard/app.py --server.port 8501
```

Ouvrez ensuite votre navigateur sur : **[http://localhost:8501](http://localhost:8501)**

---

## 7. Commandes Utiles de Vérification & Maintenance

### A. Vérifier le Nombre de Lignes dans PostgreSQL (DWH)
```bash
# Vérifier la couche Bronze
docker exec retailplus-postgres-dwh psql -U retailuser -d retailplus -c "
SELECT 'bronze.dim_magasin' AS tbl, count(*) FROM bronze.dim_magasin UNION ALL
SELECT 'bronze.fait_ventes', count(*) FROM bronze.fait_ventes;
"

# Vérifier la couche Silver & les Rejets
docker exec retailplus-postgres-dwh psql -U retailuser -d retailplus -c "
SELECT 'silver.fait_ventes' AS tbl, count(*) FROM silver.fait_ventes UNION ALL
SELECT 'silver.rejected_records', count(*) FROM silver.rejected_records;
"

# Vérifier la couche Gold (Star Schema)
docker exec retailplus-postgres-dwh psql -U retailuser -d retailplus -c "
SELECT 'gold.dim_magasin' AS tbl, count(*) FROM gold.dim_magasin UNION ALL
SELECT 'gold.dim_produit', count(*) FROM gold.dim_produit UNION ALL
SELECT 'gold.dim_temps', count(*) FROM gold.dim_temps UNION ALL
SELECT 'gold.fait_ventes', count(*) FROM gold.fait_ventes UNION ALL
SELECT 'gold.fait_retours', count(*) FROM gold.fait_retours;
"
```

### B. Tester les Requêtes du Dashboard BI
```bash
python dashboard/test_queries.py
```

### C. Voir les Logs des Conteneurs
```bash
# Logs Airflow Scheduler
docker logs -f retailplus-airflow-scheduler

# Logs Kafka Broker
docker logs -f retailplus-kafka

# Logs Spark Master
docker logs -f retailplus-spark-master
```

### D. Arrêter ou Redémarrer l'Infrastructure
```bash
# Arrêter tous les conteneurs sans perdre les données
docker compose stop

# Redémarrer les conteneurs
docker compose start

# Tout arrêter et supprimer les conteneurs
docker compose down

# Supprimer aussi les volumes de données (Remise à zéro complète)
docker compose down -v
```
