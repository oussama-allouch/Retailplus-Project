# =============================================================================
# RetailPlus — generators/gen_stock.py
# Génère la table de faits Stock (snapshot mensuel par produit × magasin).
# =============================================================================

import random
import pandas as pd
from datetime import date
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MAGASINS, DATE_DEBUT, DATE_FIN

# Snapshot le 1er de chaque mois
def _mois_entre(debut: date, fin: date) -> list[date]:
    """Retourne la liste des premiers de mois entre debut et fin."""
    mois = []
    current = debut.replace(day=1)
    while current <= fin:
        mois.append(current)
        month = current.month + 1
        year  = current.year + (1 if month > 12 else 0)
        month = month if month <= 12 else 1
        current = current.replace(year=year, month=month, day=1)
    return mois


def generate_stock(df_produits: pd.DataFrame, rng: random.Random) -> pd.DataFrame:
    """
    Génère un snapshot de stock mensuel pour chaque combinaison produit × magasin.
    Le stock varie de façon cohérente : les produits Alimentaire tournent vite,
    l'Électronique a un stock plus lent.
    """
    STOCK_INITIAL_PAR_CAT: dict[str, tuple[int, int]] = {
        "Alimentaire":  (100, 500),
        "Boissons":     (80,  400),
        "Ménager":      (50,  300),
        "Électronique": (5,   50),
        "Maison":       (10,  80),
    }

    snapshot_dates = _mois_entre(DATE_DEBUT, DATE_FIN)
    magasin_nks    = [m["magasin_nk"] for m in MAGASINS]
    rows: list[dict] = []
    sk = 1

    for _, produit in df_produits.iterrows():
        cat    = produit["categorie"]
        qte_min, qte_max = STOCK_INITIAL_PAR_CAT.get(cat, (20, 200))

        for mag_nk in magasin_nks:
            qte = rng.randint(qte_min, qte_max)   # stock initial

            for snap_date in snapshot_dates:
                # Mouvement mensuel : entre -30% et +20% du stock courant
                mouvement = int(qte * rng.uniform(-0.30, 0.20))
                qte       = max(0, qte + mouvement)

                rows.append({
                    "stock_sk":           sk,
                    "date_snapshot":      str(snap_date),
                    "produit_nk":         produit["produit_nk"],
                    "magasin_nk":         mag_nk,
                    "quantite_en_stock":  qte,
                    "valeur_stock_ht":    round(qte * produit["prix_achat_ht"], 2),
                    "seuil_reapprovisionnement": max(10, qte_min // 5),
                    "en_rupture":         qte == 0,
                })
                sk += 1

    return pd.DataFrame(rows)
