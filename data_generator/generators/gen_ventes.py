# =============================================================================
# RetailPlus — generators/gen_ventes.py
# Génère l'historique des ventes (fait_ventes + fait_retours).
# C'est le fichier le plus complexe — cœur du générateur.
# =============================================================================

import random
import pandas as pd
import numpy as np
from datetime import date, timedelta, datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    RANDOM_SEED, MAGASINS, DATE_DEBUT, DATE_FIN,
    VENTES_PAR_MAGASIN_PAR_JOUR, COEFF_MOIS, COEFF_JOUR_SEMAINE, TAUX_ERREURS,
)

# Taux de retour global (2% des lignes de vente)
TAUX_RETOUR: float = 0.02

# Motifs de retour
MOTIFS_RETOUR: list[str] = [
    "Produit défectueux", "Ne correspond pas à la description",
    "Doublon d'achat", "Changement d'avis", "Produit périmé",
]

# Heure d'achat : distribution sur les heures d'ouverture (8h–21h)
HEURES_OUVERTURE: list[int] = list(range(8, 22))
POIDS_HEURES: list[float]   = [
    0.03, 0.05, 0.08, 0.10, 0.12, 0.12,   # 8h–13h
    0.10, 0.08, 0.09, 0.10, 0.08, 0.03,   # 14h–19h
    0.01, 0.01,                             # 20h–21h
]


def _volume_journalier(current_date: date, rng: random.Random) -> int:
    """Calcule le volume de ventes pour un jour/magasin donné (avec saisonnalité)."""
    coeff = (
        COEFF_MOIS[current_date.month]
        * COEFF_JOUR_SEMAINE[current_date.weekday()]
        * rng.uniform(0.90, 1.10)   # bruit aléatoire ±10%
    )
    return max(1, int(VENTES_PAR_MAGASIN_PAR_JOUR * coeff))


def _heure_aleatoire(current_date: date, rng: random.Random) -> str:
    """Génère un timestamp réaliste dans la journée."""
    heure   = rng.choices(HEURES_OUVERTURE, weights=POIDS_HEURES, k=1)[0]
    minute  = rng.randint(0, 59)
    seconde = rng.randint(0, 59)
    return f"{current_date}T{heure:02d}:{minute:02d}:{seconde:02d}"


def generate_ventes(
    df_clients:  pd.DataFrame,
    df_produits: pd.DataFrame,
    rng:         random.Random,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Génère l'historique complet des ventes sur 12 mois.

    Retourne :
        (df_ventes, df_retours)

    Logique de génération :
    - Pour chaque jour × magasin, on calcule le volume avec saisonnalité
    - Les produits suivent une loi de Pareto : 20% des produits = 80% des ventes
    - Les clients Premium achètent plus souvent (distribution non-uniforme)
    - Des erreurs intentionnelles sont injectées (doublons, qtés négatives, etc.)
    """
    ventes:  list[dict] = []
    retours: list[dict] = []

    magasin_nks   = [m["magasin_nk"] for m in MAGASINS]
    client_nks    = df_clients["client_nk"].tolist()
    produit_rows  = df_produits[["produit_nk", "prix_vente_ht", "prix_vente_ttc",
                                  "prix_achat_ht", "tva_pct"]].to_dict("records")

    # Pareto : les 20% premiers produits ont 5× plus de chances d'être vendus
    nb_produits   = len(produit_rows)
    top_20_pct    = max(1, int(nb_produits * 0.20))
    poids_produits = [5.0] * top_20_pct + [1.0] * (nb_produits - top_20_pct)
    total_poids    = sum(poids_produits)
    poids_produits = [p / total_poids for p in poids_produits]

    import itertools
    cum_poids_produits = list(itertools.accumulate(poids_produits))

    # Choisir le client (les 10% premiers = Premium -> 3x plus de chance)
    nb_premium = int(len(client_nks) * 0.10)
    poids_cl   = [3.0] * nb_premium + [1.0] * (len(client_nks) - nb_premium)
    total_cl   = sum(poids_cl)
    poids_cl   = [p / total_cl for p in poids_cl]
    cum_poids_cl = list(itertools.accumulate(poids_cl))

    vente_sk  = 1
    retour_sk = 1
    ticket_counter = 1

    current = DATE_DEBUT
    while current <= DATE_FIN:
        for mag_nk in magasin_nks:
            nb_tickets = _volume_journalier(current, rng)

            for _ in range(nb_tickets):
                ticket_nk  = f"TKT-{mag_nk}-{current.strftime('%Y%m%d')}-{ticket_counter:06d}"
                ticket_counter += 1

                client_nk  = rng.choices(client_nks, cum_weights=cum_poids_cl, k=1)[0]

                # Injecter un client fantôme (1%)
                if rng.random() < TAUX_ERREURS["client_inexistant"]:
                    client_nk = "CLI-FANTOME"

                # Nombre de produits par ticket (1 à 8, moyenne ~3)
                nb_lignes = rng.choices([1,2,3,4,5,6,7,8], weights=[5,12,20,20,18,12,8,5], k=1)[0]
                produits_ticket = rng.choices(produit_rows, cum_weights=cum_poids_produits, k=nb_lignes)

                timestamp = _heure_aleatoire(current, rng)

                for prod in produits_ticket:
                    quantite   = rng.randint(1, 5)
                    prix_ht    = prod["prix_vente_ht"]
                    prix_ttc   = prod["prix_vente_ttc"]
                    marge_unit = round(prix_ht - prod["prix_achat_ht"], 2)

                    # ── Injections d'erreurs ───────────────────────────────
                    if rng.random() < TAUX_ERREURS["quantite_negative"]:
                        quantite = rng.choice([-1, -2, 0])         # quantité invalide
                    if rng.random() < TAUX_ERREURS["prix_negatif"]:
                        prix_ht  = round(-abs(prix_ht), 2)         # prix négatif
                        prix_ttc = round(-abs(prix_ttc), 2)
                    if rng.random() < TAUX_ERREURS["date_malformee"]:
                        timestamp = "DATE_INVALIDE"                 # date corrompue

                    montant_ht  = round(prix_ht * quantite, 2)
                    montant_ttc = round(prix_ttc * quantite, 2)

                    row = {
                        "vente_sk":         vente_sk,
                        "ticket_nk":        ticket_nk,
                        "timestamp_vente":  timestamp,
                        "date_vente":       str(current),
                        "magasin_nk":       mag_nk,
                        "client_nk":        client_nk,
                        "produit_nk":       prod["produit_nk"],
                        "quantite":         quantite,
                        "prix_unitaire_ht": prix_ht,
                        "tva_pct":          prod["tva_pct"],
                        "prix_unitaire_ttc":prix_ttc,
                        "montant_ht":       montant_ht,
                        "montant_ttc":      montant_ttc,
                        "marge_brute_unit": marge_unit,
                        "marge_brute_total":round(marge_unit * max(1, quantite), 2),
                    }

                    ventes.append(row)

                    # Doublon intentionnel (3%)
                    if rng.random() < TAUX_ERREURS["doublons"]:
                        doublon = row.copy()
                        doublon["vente_sk"] = -vente_sk   # SK négatif = marqueur doublon
                        ventes.append(doublon)

                    vente_sk += 1

        # Avancer au jour suivant
        current += timedelta(days=1)

    df_ventes = pd.DataFrame(ventes)

    # ── Génération des retours (2% des lignes de vente valides) ──────────────
    ventes_valides = df_ventes[
        (df_ventes["vente_sk"] > 0) &
        (df_ventes["quantite"] > 0)
    ]
    nb_retours = int(len(ventes_valides) * TAUX_RETOUR)
    sample_retours = ventes_valides.sample(n=nb_retours, random_state=RANDOM_SEED)

    retours_list: list[dict] = []
    for _, vente in sample_retours.iterrows():
        retour_date = date.fromisoformat(vente["date_vente"]) + timedelta(days=rng.randint(1, 30))
        if retour_date > DATE_FIN:
            retour_date = DATE_FIN

        retours_list.append({
            "retour_sk":            retour_sk,
            "retour_nk":            f"RET-{retour_sk:07d}",
            "ticket_nk":            vente["ticket_nk"],
            "produit_nk":           vente["produit_nk"],
            "magasin_nk":           vente["magasin_nk"],
            "client_nk":            vente["client_nk"],
            "date_vente_originale": vente["date_vente"],
            "date_retour":          str(retour_date),
            "quantite_retournee":   vente["quantite"],
            "montant_rembourse":    vente["montant_ttc"],
            "motif":                rng.choice(MOTIFS_RETOUR),
        })
        retour_sk += 1

    df_retours = pd.DataFrame(retours_list)

    from config import RANDOM_SEED as _seed
    return df_ventes, df_retours


def update_segments_clients(df_clients: pd.DataFrame, df_ventes: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule le segment de chaque client à partir de l'historique de ventes.
    Remplace la valeur 'À calculer' dans dim_client.
    """
    ventes_valides = df_ventes[(df_ventes["vente_sk"] > 0) & (df_ventes["quantite"] > 0)]

    stats = (
        ventes_valides.groupby("client_nk")
        .agg(
            nb_tickets  = ("ticket_nk", "nunique"),
            panier_moy  = ("montant_ttc", "mean"),
        )
        .reset_index()
    )

    def attribuer_segment(row) -> str:
        if row["panier_moy"] >= 500 and row["nb_tickets"] >= 48:   # ~4/mois × 12
            return "Premium"
        elif row["panier_moy"] >= 150 and row["nb_tickets"] >= 12:  # ~1/mois × 12
            return "Standard"
        else:
            return "Occasionnel"

    stats["segment"] = stats.apply(attribuer_segment, axis=1)

    df_merged = df_clients.merge(
        stats[["client_nk", "segment"]].rename(columns={"segment": "segment_calcule"}),
        on="client_nk", how="left"
    )
    df_merged["segment"] = df_merged["segment_calcule"].fillna("Occasionnel")
    df_merged.drop(columns=["segment_calcule"], inplace=True)
    return df_merged
