# =============================================================================
# RetailPlus — generators/gen_commandes.py
# Génère les commandes fournisseurs (réapprovisionnements).
# =============================================================================

import random
import uuid
import pandas as pd
from datetime import date, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MAGASINS, DATE_DEBUT, DATE_FIN

STATUTS_COMMANDE: list[str] = ["LIVREE", "LIVREE", "LIVREE", "EN_TRANSIT", "ANNULEE"]
# Distribution : 60% livrées, 20% en transit, 20% annulées


def generate_commandes(
    df_produits: pd.DataFrame,
    df_fournisseurs: pd.DataFrame,
    rng: random.Random,
) -> pd.DataFrame:
    """
    Génère ~2 000 commandes fournisseurs.
    Chaque commande contient plusieurs lignes produits (1 à 15).
    Les délais de livraison viennent de dim_fournisseur.
    """
    commandes:  list[dict] = []
    lignes:     list[dict] = []
    commande_sk = 1
    ligne_sk    = 1

    magasin_nks = [m["magasin_nk"] for m in MAGASINS]

    # Index fournisseur → délai
    delai_par_fournisseur = dict(
        zip(df_fournisseurs["fournisseur_nk"], df_fournisseurs["delai_livraison_jours"])
    )

    nb_commandes_target = 2_000
    periode_jours       = (DATE_FIN - DATE_DEBUT).days

    for _ in range(nb_commandes_target):
        fournisseur_row = df_fournisseurs.sample(1, random_state=rng.randint(0, 99999)).iloc[0]
        fournisseur_nk  = fournisseur_row["fournisseur_nk"]
        magasin_nk      = rng.choice(magasin_nks)
        delai           = delai_par_fournisseur.get(fournisseur_nk, 5)

        date_commande   = DATE_DEBUT + timedelta(days=rng.randint(0, periode_jours - delai))
        date_livraison  = date_commande + timedelta(days=delai + rng.randint(0, 2))
        statut          = rng.choice(STATUTS_COMMANDE)
        commande_nk     = f"CMD-{commande_sk:06d}"

        # Produits du fournisseur uniquement (cohérence référentielle)
        produits_four = df_produits[df_produits["fournisseur_nk"] == fournisseur_nk]
        if produits_four.empty:
            produits_four = df_produits

        nb_lignes      = rng.randint(1, min(15, len(produits_four)))
        sample_produits = produits_four.sample(nb_lignes, random_state=rng.randint(0, 99999))
        montant_total   = 0.0

        for _, prod in sample_produits.iterrows():
            qte        = rng.randint(10, 200)
            prix_pu    = prod["prix_achat_ht"]
            montant_l  = round(qte * prix_pu, 2)
            montant_total += montant_l

            lignes.append({
                "ligne_commande_sk":    ligne_sk,
                "commande_nk":          commande_nk,
                "produit_nk":           prod["produit_nk"],
                "quantite_commandee":   qte,
                "prix_unitaire_achat":  prix_pu,
                "montant_ligne_ht":     montant_l,
            })
            ligne_sk += 1

        commandes.append({
            "commande_sk":          commande_sk,
            "commande_nk":          commande_nk,
            "fournisseur_nk":       fournisseur_nk,
            "magasin_nk":           magasin_nk,
            "date_commande":        str(date_commande),
            "date_livraison_prev":  str(date_livraison),
            "statut":               statut,
            "montant_total_ht":     round(montant_total, 2),
        })
        commande_sk += 1

    return pd.DataFrame(commandes), pd.DataFrame(lignes)
