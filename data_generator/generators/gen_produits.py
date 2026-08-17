# =============================================================================
# RetailPlus — generators/gen_produits.py
# Génère la dimension Produit (500 produits répartis en 17 sous-catégories).
# =============================================================================

import random
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RANDOM_SEED, NB_PRODUITS, CATALOGUE_PRODUITS

# Noms de produits réalistes par sous-catégorie
NOMS_PRODUITS: dict[str, list[str]] = {
    "Céréales & Féculents":    ["Farine", "Riz", "Pâtes", "Couscous", "Lentilles", "Pois chiches", "Farine complète", "Riz basmati", "Semoule", "Vermicelles"],
    "Viandes & Poissons":      ["Poulet", "Boeuf haché", "Agneau", "Sardines", "Thon en boîte", "Escalope", "Côtelettes", "Filet de merlan", "Crevettes", "Calamars"],
    "Produits laitiers":       ["Lait entier", "Fromage blanc", "Yaourt nature", "Beurre", "Crème fraîche", "Fromage fondu", "Lait écrémé", "Yaourt aromatisé"],
    "Fruits & Légumes":        ["Tomates", "Pommes de terre", "Oignons", "Carottes", "Poivrons", "Courgettes", "Pommes", "Bananes", "Oranges", "Concombres"],
    "Conserves & Épices":      ["Conserve tomates", "Harissa", "Cumin", "Paprika", "Curcuma", "Cannelle", "Ras el Hanout", "Olives en bocal", "Cornichons"],
    "Eaux & Jus":              ["Eau minérale 1.5L", "Eau gazeuse", "Jus d'orange", "Jus de raisin", "Nectar abricot", "Eau plate 0.5L", "Jus de pomme"],
    "Sodas":                   ["Cola 1.5L", "Limonade", "Orangeade", "Soda citron", "Cola Light", "Energy drink", "Soda gingembre"],
    "Boissons chaudes":        ["Café moulu", "Thé vert", "Thé à la menthe", "Nescafé", "Café soluble", "Infusion camomille", "Thé noir"],
    "Nettoyage":               ["Détergent linge", "Liquide vaisselle", "Javel", "Désinfectant", "Nettoyant multi-surfaces", "Poudre à lessive", "Assouplissant"],
    "Hygiène":                 ["Shampoing", "Gel douche", "Savon solide", "Dentifrice", "Déodorant", "Brosse à dents", "Coton-tiges", "Rasoir"],
    "Entretien":               ["Sacs poubelles", "Éponges", "Papier alu", "Film alimentaire", "Papier absorbant", "Balai", "Serpillère"],
    "Petit électroménager":    ["Grille-pain", "Bouilloire", "Mixer", "Cafetière", "Fer à repasser", "Aspirateur compact", "Ventilateur"],
    "Audio & Vidéo":           ["Écouteurs", "Haut-parleur Bluetooth", "Casque audio", "Câble HDMI", "Clé USB", "Chargeur rapide", "Support téléphone"],
    "Informatique":            ["Souris sans-fil", "Clavier USB", "Webcam", "Hub USB", "Câble USB-C", "Tapis de souris", "Lampe de bureau LED"],
    "Cuisine":                 ["Casserole", "Poêle", "Saladier", "Couteau de chef", "Planche à découper", "Économiseur", "Set à épices"],
    "Décoration":              ["Coussin déco", "Cadre photo", "Bougie parfumée", "Vase", "Miroir rond", "Tapis salon", "Guirlande lumineuse"],
    "Linge de maison":         ["Drap housse", "Taie d'oreiller", "Serviette bain", "Couverture polaire", "Rideau", "Nappe", "Essuie-mains"],
}

# Prix d'achat HT (fourchette) par catégorie principale
PRIX_ACHAT_PAR_CATEGORIE: dict[str, tuple[float, float]] = {
    "Alimentaire":  (2.0,   85.0),
    "Boissons":     (3.0,   60.0),
    "Ménager":      (5.0,   120.0),
    "Électronique": (80.0,  2_000.0),
    "Maison":       (30.0,  600.0),
}


def generate_produits(rng: random.Random) -> pd.DataFrame:
    """
    Génère 500 produits répartis selon CATALOGUE_PRODUITS.
    La marge est comprise entre 15% et 40% (marge brute réaliste grande distribution).
    """
    produits: list[dict] = []
    produit_sk = 1
    produit_counter = 1

    for (categorie, sous_cat, nb, fournisseur_nk, tva_pct) in CATALOGUE_PRODUITS:
        noms_disponibles = NOMS_PRODUITS.get(sous_cat, ["Produit"])
        prix_min, prix_max = PRIX_ACHAT_PAR_CATEGORIE.get(categorie, (5.0, 100.0))

        for _ in range(nb):
            nom_base  = rng.choice(noms_disponibles)
            variante  = rng.randint(1, 99)
            nom       = f"{nom_base} {variante:02d}"

            prix_achat_ht  = round(rng.uniform(prix_min, prix_max), 2)
            marge_pct      = rng.uniform(0.15, 0.40)            # marge 15–40%
            prix_vente_ht  = round(prix_achat_ht * (1 + marge_pct), 2)
            prix_vente_ttc = round(prix_vente_ht * (1 + tva_pct / 100), 2)
            marge_brute    = round(prix_vente_ht - prix_achat_ht, 2)

            produits.append({
                "produit_sk":       produit_sk,
                "produit_nk":       f"PROD-{produit_counter:05d}",
                "nom":              nom,
                "categorie":        categorie,
                "sous_categorie":   sous_cat,
                "fournisseur_nk":   fournisseur_nk,
                "prix_achat_ht":    prix_achat_ht,
                "prix_vente_ht":    prix_vente_ht,
                "tva_pct":          tva_pct,
                "prix_vente_ttc":   prix_vente_ttc,
                "marge_brute_ht":   marge_brute,
                "est_actif":        True,
            })
            produit_sk      += 1
            produit_counter += 1

    df = pd.DataFrame(produits)
    return df
