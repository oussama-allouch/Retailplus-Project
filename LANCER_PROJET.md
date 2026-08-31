# ⚡ Commandes pour Lancer le Projet (RetailPlus)

Ce fichier contient uniquement les commandes exactes à exécuter dans votre terminal (PowerShell ou Bash) pour démarrer la plateforme et ses services sur votre machine.

---

## 1. Démarrer l'Infrastructure Complète (Docker)

```powershell
docker compose up -d
```

---

## 2. Vérifier l'État des Conteneurs

```powershell
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

---

## 3. Lancer le Dashboard Décisionnel BI (Streamlit)

```powershell
streamlit run dashboard/app.py --server.port 8501
```

> 🌐 **Accès au Dashboard :** [http://localhost:8501](http://localhost:8501)

---

## 4. Accéder aux Interfaces Web

| Service | URL | Identifiants |
|---|---|---|
| 📊 **Dashboard BI (Streamlit)** | [http://localhost:8501](http://localhost:8501) | *Sans mot de passe* |
| 🌪️ **Airflow Orchestrator** | [http://localhost:8081](http://localhost:8081) | `admin` / `admin` |
| ⚡ **Spark Master** | [http://localhost:8080](http://localhost:8080) | — |
| 🐘 **PostgreSQL DWH** | `localhost:5434` (`retailplus`) | `retailuser` / `retailpassword` |

---

## 5. (Optionnel) Déclencher le Pipeline de Données de Bout en Bout

Si vous souhaitez relancer l'ingestion, le nettoyage et la modélisation :

```powershell
docker exec retailplus-airflow-webserver airflow dags trigger dag_retailplus_master
```

---

## 6. (Optionnel) Lancer le Simulateur de Ventes en Temps Réel (Kafka Streaming)

```powershell
python data_generator/run_simulator.py --events 500 --interval 0.5
```

---

## 7. Arrêter le Projet

```powershell
# Arrêter les conteneurs proprement
docker compose stop

# Tout éteindre et supprimer les conteneurs
docker compose down
```
