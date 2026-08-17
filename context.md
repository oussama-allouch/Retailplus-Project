# Fichier de Contexte du Projet -- RetailPlus

Ce fichier centralise l'état d'avancement, l'architecture globale, le modèle de données, et l'historique des étapes validées de la plateforme de données **RetailPlus**. Il sert de référence pour maintenir la cohérence du projet au fil de son développement.

---

## 1. Vision Globale du Projet

**RetailPlus** est une plateforme moderne de données (Data Platform) destinée à une chaîne de grande distribution marocaine (5 magasins physiques répartis dans plusieurs villes). 
La plateforme a pour but de :
* Consommer des données historiques volumineuses (Batch) pour l'analyse décisionnelle.
* Capturer et traiter des données de caisse en temps réel (Streaming).
* Nettoyer, enrichir et modéliser ces données pour créer des dashboards analytiques de performance commerciale, gestion des stocks, et comportement client.

---

## 2. Architecture Globale de la Plateforme

L'architecture suit un modèle de **Médaillon (Bronze → Silver → Gold)** alimenté par des pipelines Batch et Streaming.

```mermaid
graph TD
    %% Sources
    subgraph Sources de Données
        CSV[Historique CSV - Batch]
        Producer[Simulateur Python] -->|JSON| Kafka[Apache Kafka - Streaming]
    end

    %% Ingestion
    subgraph Ingestion & Stockage (Bronze)
        CSV -->|Spark Batch| PG_Bronze[PostgreSQL Bronze]
        Kafka -->|Spark Structured Streaming| PG_Bronze
    end

    %% Transformation
    subgraph Nettoyage & Qualité (Silver)
        PG_Bronze -->|Spark Processing & Clean| PG_Silver[PostgreSQL Silver]
    end

    %% Modélisation
    subgraph Modélisation & Décisionnel (Gold)
        PG_Silver -->|Spark Dimension & Fact Models| PG_Gold[PostgreSQL Gold]
    end

    %% Restitution
    subgraph Restitution
        PG_Gold --> BI[Outils de BI / PowerBI / Superset]
    end

    %% Orchestration
    Airflow[Apache Airflow] -.->|Orchestration & Dags| Ingestion
    Airflow -.->|Orchestration & Dags| Transformation
    Airflow -.->|Orchestration & Dags| Modélisation
```

### Stack Technique :
* **Ingestion Temps Réel** : Apache Kafka (Topics `retailplus.ventes` et `retailplus.retours`).
* **Traitement & Transformations** : Apache Spark (Spark SQL & Spark Streaming en Python/PySpark).
* **Orchestration** : Apache Airflow.
* **Stockage / Data Warehouse** : PostgreSQL (divisé en trois schémas : `bronze`, `silver`, `gold`).
* **Infrastructure** : Docker & Docker Compose.

---

## 3. Modélisation des Données (Schéma en Étoile - Couche Gold)

Le schéma modélise les ventes, les retours de marchandises, les mouvements de stocks, et les commandes auprès des fournisseurs.

### Tables de Dimensions :
1. **`dim_magasin`** : Informations sur les points de vente (surface, ville, type).
2. **`dim_produit`** : Référentiel des articles avec prix d'achat, prix de vente HT/TTC, catégorie, et fournisseur associé.
3. **`dim_client`** : Base clients enrichie avec leur profil et leur segment de fidélité.
4. **`dim_fournisseur`** : Liste des partenaires d'approvisionnement et délais de livraison moyens.
5. **`dim_temps`** : Calendrier enrichi (jours fériés marocains, weekends, trimestres).

### Tables de Faits :
1. **`fait_ventes`** : Enregistrement de chaque ligne de ticket de caisse (quantités, montants HT/TTC, marges).
2. **`fait_retours`** : Détail des retours clients (produit retourné, quantité, motif, remboursement).
3. **`fait_stock`** : Instantanés (snapshots) mensuels des stocks par produit et par magasin.
4. **`fait_commandes`** : Suivi des réapprovisionnements auprès des fournisseurs.

---

## 4. Étapes Validées du Projet

### Étape 1 : Cadrage et Architecture (Validée)
* Définition des besoins fonctionnels et de l'architecture cible.

### Étape 2 : Modélisation Conceptuelle (Validée)
* Conception du schéma relationnel en étoile et définition des contraintes référentielles.

### Étape 3 : Spécification des Flux (Validée)
* Définition des cinétiques d'ingestion (Kafka streaming vs CSV Batch).

### Étape 4 : Générateur de Données Simulées (Validée & Générée)
* **Emplacement du code** : [data_generator/](file:///C:/Users/OUSSAMA/Desktop/AISD%20master/PFA/RetailPlus%20Project/data_generator)
* **Volumes générés avec succès** :
  * `dim_magasin.csv` : 5 magasins physiques (Casablanca, Rabat, Marrakech, Fès, Tanger).
  * `dim_fournisseur.csv` : 8 fournisseurs nationaux et internationaux.
  * `dim_produit.csv` : 500 produits répartis de façon réaliste par catégorie (Alimentaire, Boissons, Électronique, Maison, Ménager).
  * `dim_client.csv` : 10 000 clients marocains. Segmentation finale calculée et affectée en fonction des achats réels (*Premium*, *Standard*, *Occasionnel*).
  * `dim_temps.csv` : 366 lignes (Année 2024 complète, incluant weekends et jours fériés nationaux).
  * `fait_stock.csv` : 30 000 snapshots mensuels de stocks.
  * `fait_commandes.csv` : 2 000 bons de commande fournisseurs.
  * `fait_lignes_commandes.csv` : 15 811 lignes de détail d'approvisionnements.
  * `fait_ventes.csv` : **4 255 379 transactions** (Simulant la saisonnalité de 2024 avec pics pendant le Ramadan, la période estivale et les fêtes de fin d'année ; distribution de popularité des produits selon la loi de Pareto).
  * `fait_retours.csv` : 80 985 lignes de retours (soit ~2% des ventes valides).

* **Erreurs intentionnellement injectées dans la couche brute (Bronze) pour valider le futur pipeline de nettoyage (Silver)** :
  * Doublons ventes : 123 675 lignes dupliquées.
  * Quantités invalides (négatives ou nulles) : 84 906 transactions.
  * Prix de vente corrompus (négatifs) : 97 644 transactions.
  * Emails clients mal formés : 489 clients.
  * Date/Heures invalides : Injectées de manière aléatoire.
  * Identifiants clients non référencés : Clientes "fantômes" pour tester la robustesse des jointures.

---

### Étape 5 : Mise en place de l'environnement Docker (Validée)
* **Configuration** : Fichier [docker-compose.yml](file:///C:/Users/OUSSAMA/Desktop/AISD%20master/PFA/RetailPlus%20Project/docker-compose.yml) complet orchestrant 8 conteneurs sur le réseau `retailplus-net`.
* **Database (PostgreSQL DWH)** : Conteneur `retailplus-postgres-dwh` (PostgreSQL 15 sur port `5432`). Initialisé via [init.sql](file:///C:/Users/OUSSAMA/Desktop/AISD%20master/PFA/RetailPlus%20Project/docker/postgres/init.sql) avec les schémas `bronze`, `silver`, `gold` et leurs 31 tables respectives.
* **Streaming (Kafka & Zookeeper)** : Conteneurs `retailplus-zookeeper` et `retailplus-kafka` (port `9092`). Topics créés et vérifiés : `retailplus.ventes` et `retailplus.retours`.
* **Traitement (Apache Spark)** : Conteneurs `retailplus-spark-master` (`apache/spark:3.5.9` sur port `7077`, UI sur `http://localhost:8080`) et `retailplus-spark-worker` (connecté avec 2 cores et 2 Go RAM).
* **Orchestration (Apache Airflow)** : Conteneurs `retailplus-airflow-db` (Postgres dédié sur port `5433`), `retailplus-airflow-init` (création utilisateur admin), `retailplus-airflow-webserver` (UI sur `http://localhost:8081`, login `admin`/`admin`), et `retailplus-airflow-scheduler`.

---

### Étape 6 : Pipeline d'Ingestion Batch & Streaming (Couche Bronze) (Validée)
* **Ingestion Batch (Dimensions & Faits)** :
  * Développé les scripts [ingest_referentiels.py](file:///C:/Users/OUSSAMA/Desktop/AISD%20master/PFA/RetailPlus%20Project/spark_jobs/batch/ingest_referentiels.py) et [ingest_transactions.py](file:///C:/Users/OUSSAMA/Desktop/AISD%20master/PFA/RetailPlus%20Project/spark_jobs/batch/ingest_transactions.py).
  * Chargé avec succès l'ensemble des référentiels (10 879 lignes) et des faits historiques (4 384 175 lignes) depuis les fichiers CSV vers le schéma `bronze` de PostgreSQL.
* **Ingestion Streaming (Temps Réel)** :
  * Développé le job Structured Streaming [ingest_kafka_ventes.py](file:///C:/Users/OUSSAMA/Desktop/AISD%20master/PFA/RetailPlus%20Project/spark_jobs/streaming/ingest_kafka_ventes.py) s'exécutant sur le cluster Spark.
  * Consomme en continu les topics Kafka `retailplus.ventes` et `retailplus.retours` pour alimenter les tables `bronze.fait_ventes` et `bronze.fait_retours`.
  * Testé avec succès en parallèle avec le simulateur [run_simulator.py](file:///C:/Users/OUSSAMA/Desktop/AISD%20master/PFA/RetailPlus%20Project/data_generator/run_simulator.py).

---

### Étape 7 : Pipeline de Transformation & Nettoyage (Couche Silver) (Validée)
* **Contrôle Qualité & Gouvernance** :
  * Développé les modules PySpark [quality_checks.py](file:///C:/Users/OUSSAMA/Desktop/AISD%20master/PFA/RetailPlus%20Project/spark_jobs/utils/quality_checks.py), [clean_dimensions.py](file:///C:/Users/OUSSAMA/Desktop/AISD%20master/PFA/RetailPlus%20Project/spark_jobs/silver/clean_dimensions.py), [clean_transactions.py](file:///C:/Users/OUSSAMA/Desktop/AISD%20master/PFA/RetailPlus%20Project/spark_jobs/silver/clean_transactions.py) et l'orchestrateur [run_silver_pipeline.py](file:///C:/Users/OUSSAMA/Desktop/AISD%20master/PFA/RetailPlus%20Project/spark_jobs/silver/run_silver_pipeline.py).
* **Résultats obtenus sur ~4.4M d'enregistrements** :
  * 3 970 815 enregistrements nettoyés, typés et validés insérés dans les 10 tables du schéma `silver`.
  * 289 236 enregistrements non conformes (quantités négatives, montants invalides, clients fantômes) correctement redirigés vers la table `silver.rejected_records` avec motif explicite.
  * 123 675 lignes de ventes en doublon éliminées lors de la déduplication.

---

### Étape 8 : Modélisation & Chargement du Data Warehouse (Couche Gold) (Validée)
* **Schéma en Étoile & Surrogate Keys (`_sk`)** :
  * Développé les jobs PySpark [build_dimensions_gold.py](file:///C:/Users/OUSSAMA/Desktop/AISD%20master/PFA/RetailPlus%20Project/spark_jobs/gold/build_dimensions_gold.py), [build_facts_gold.py](file:///C:/Users/OUSSAMA/Desktop/AISD%20master/PFA/RetailPlus%20Project/spark_jobs/gold/build_facts_gold.py) et l'orchestrateur [run_gold_pipeline.py](file:///C:/Users/OUSSAMA/Desktop/AISD%20master/PFA/RetailPlus%20Project/spark_jobs/gold/run_gold_pipeline.py).
  * Généré les Surrogate Keys pour toutes les dimensions et mappé les clés étrangères `_sk` sur l'intégralité des tables de faits (`fait_stock`, `fait_commandes`, `fait_lignes_commandes`, `fait_ventes`, `fait_retours`).
  * Concordance exacte à 100% des volumes de données entre Silver et Gold (3,97 millions de lignes au total).
  * Validation des requêtes BI analytiques décisionnelles en étoile.

---

### Étape 9 : Orchestration Globale des DAGs Apache Airflow (Validée)
* **Architecture & Orchestration Conteneurisée** :
  * Montage du socket Docker (`/var/run/docker.sock`) dans [docker-compose.yml](file:///C:/Users/OUSSAMA/Desktop/AISD%20master/PFA/RetailPlus%20Project/docker-compose.yml) pour permettre aux DAGs d'exécuter des jobs PySpark via `DockerOperator`.
  * Développé [dag_bronze_ingestion.py](file:///C:/Users/OUSSAMA/Desktop/AISD%20master/PFA/RetailPlus%20Project/airflow/dags/dag_bronze_ingestion.py) : Ingestion batch CSV → Bronze (référentiels + faits).
  * Développé [dag_silver_transformation.py](file:///C:/Users/OUSSAMA/Desktop/AISD%20master/PFA/RetailPlus%20Project/airflow/dags/dag_silver_transformation.py) : Nettoyage, typage fort, déduplication et routage des rejets.
  * Développé [dag_gold_warehouse.py](file:///C:/Users/OUSSAMA/Desktop/AISD%20master/PFA/RetailPlus%20Project/airflow/dags/dag_gold_warehouse.py) : Purge (`TRUNCATE CASCADE`), génération des SKs et alimentation du Star Schema.
  * Développé [dag_retailplus_master.py](file:///C:/Users/OUSSAMA/Desktop/AISD%20master/PFA/RetailPlus%20Project/airflow/dags/dag_retailplus_master.py) : Orchestrateur E2E chaînant Bronze → Silver → Gold via `TriggerDagRunOperator`.
  * Détection à 100% sans erreur d'import et activation réussie des 4 DAGs dans l'interface Web Airflow (`http://localhost:8081`).

---

## 5. Prochaine Étape

### Étape 10 : Vues Analytiques & Tableaux de Bord Décisionnels (BI & Data Visualization)
* Développer les vues SQL décisionnelles ou rapports analytiques (Performance Magasins, Comportement Clients, Gestion des Stocks, Analyse des Retours).
* Créer des dashboards / interfaces de visualisation de données branchées directement sur le schéma `gold`.
