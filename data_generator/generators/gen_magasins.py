# =============================================================================
# RetailPlus — generators/gen_magasins.py
# Génère la dimension Magasin (données manuelles, stables).
# =============================================================================

import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MAGASINS


def generate_magasins() -> pd.DataFrame:
    """
    Retourne le DataFrame dim_magasin.
    Les magasins sont définis manuellement — ce sont des données de référence
    stables qui ne changent pas entre les exécutions.
    """
    df = pd.DataFrame(MAGASINS)

    # Ajout d'une clé surrogate entière (SK) pour le Data Warehouse
    df.insert(0, "magasin_sk", range(1, len(df) + 1))

    # Colonnes d'audit
    df["date_creation"]      = "2024-01-01"
    df["est_actif"]          = True

    column_order = [
        "magasin_sk", "magasin_nk", "nom", "ville", "region",
        "type", "surface_m2", "date_creation", "est_actif",
    ]
    return df[column_order]
