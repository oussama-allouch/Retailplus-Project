# =============================================================================
# RetailPlus — run_simulator.py
# Script de lancement du simulateur temps réel (Kafka).
# =============================================================================

import os
import sys
import pandas as pd

# Ajout des chemins pour les imports
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "kafka_producer"))

from producer import run_producer

def main():
    print("=" * 70)
    print("  RetailPlus — Lancement du Simulateur Temps Réel Kafka")
    print("=" * 70)
    
    csv_client_path = os.path.join(BASE_DIR, "output", "csv", "dim_client.csv")
    csv_produit_path = os.path.join(BASE_DIR, "output", "csv", "dim_produit.csv")
    
    if not os.path.exists(csv_client_path) or not os.path.exists(csv_produit_path):
        print("[ERROR] Fichiers CSV introuvables. Lancez d'abord main.py pour les generer.")
        sys.exit(1)
        
    print(">> Chargement des donnees de reference...")
    df_clients = pd.read_csv(csv_client_path)
    df_produits = pd.read_csv(csv_produit_path)
    
    print(f"   [OK] {len(df_clients):,} clients charges.")
    print(f"   [OK] {len(df_produits):,} produits charges.")
    
    print("\n>> Demarrage de la simulation...")
    # use_kafka=True pour envoyer vers Kafka (KAFKA_BOOTSTRAP_SERVERS par défaut localhost:9092)
    run_producer(df_clients, df_produits, use_kafka=True)

if __name__ == "__main__":
    main()
