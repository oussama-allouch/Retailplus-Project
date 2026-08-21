# =============================================================================
# RetailPlus — dashboard/test_queries.py
# Script de test automatisé des requêtes du connecteur BI
# =============================================================================

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_connector import (
    get_kpis_globaux,
    get_ventes_mensuelles,
    get_performance_magasins,
    get_performance_produits,
    get_ventes_par_categorie,
    get_segmentation_clients,
    get_top_clients,
    get_gestion_stocks,
    get_analyse_retours
)

def run_tests():
    print("=" * 60)
    print("  RetailPlus — Test des Requêtes Dashboard BI (Gold DWH)")
    print("=" * 60)
    
    tests = [
        ("1. KPIs Globaux", get_kpis_globaux),
        ("2. Ventes Mensuelles", get_ventes_mensuelles),
        ("3. Performance Magasins", get_performance_magasins),
        ("4. Performance Produits", get_performance_produits),
        ("5. Ventes par Catégorie", get_ventes_par_categorie),
        ("6. Segmentation Clients", get_segmentation_clients),
        ("7. Top Clients", get_top_clients),
        ("8. Gestion Stocks", get_gestion_stocks),
        ("9. Analyse Retours", get_analyse_retours),
    ]
    
    all_ok = True
    for name, func in tests:
        try:
            df = func()
            print(f"  [OK] {name:<30} : {len(df):>6} lignes récupérées")
        except Exception as e:
            print(f"  [FAIL] {name:<28} : Erreur: {e}")
            all_ok = False
            
    print("=" * 60)
    if all_ok:
        print("  TOUTES LES REQUÊTES DU DASHBOARD SONT VALIDÉES ! [100% OK]")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
