# =============================================================================
# RetailPlus — generators/gen_fournisseurs.py
# Génère la dimension Fournisseur (données manuelles, stables).
# =============================================================================

import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import FOURNISSEURS


def generate_fournisseurs() -> pd.DataFrame:
    """
    Retourne le DataFrame dim_fournisseur.
    Les fournisseurs sont définis manuellement — partenaires commerciaux réels
    inspirés des grandes entreprises au Maroc.
    """
    df = pd.DataFrame(FOURNISSEURS)

    # Clé surrogate
    df.insert(0, "fournisseur_sk", range(1, len(df) + 1))

    # Colonnes d'audit
    df["date_debut_contrat"] = "2023-01-01"
    df["est_actif"]          = True

    column_order = [
        "fournisseur_sk", "fournisseur_nk", "nom", "categorie_principale",
        "pays", "delai_livraison_jours", "date_debut_contrat", "est_actif",
    ]
    return df[column_order]
