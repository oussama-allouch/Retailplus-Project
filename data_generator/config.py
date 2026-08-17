# =============================================================================
# RetailPlus — config.py
# Cerveau du générateur : tous les paramètres sont ici.
# Modifier UNIQUEMENT ce fichier pour changer les volumes ou la période.
# =============================================================================

from datetime import date

# ─── Reproductibilité ────────────────────────────────────────────────────────
# Un seed fixe garantit des données identiques à chaque exécution.
# Indispensable pour déboguer un pipeline sans changer les données source.
RANDOM_SEED: int = 42

# ─── Période historique ──────────────────────────────────────────────────────
DATE_DEBUT: date = date(2024, 1, 1)
DATE_FIN:   date = date(2024, 12, 31)   # 12 mois d'historique complet

# ─── Volumes ─────────────────────────────────────────────────────────────────
NB_CLIENTS:      int = 10_000
NB_PRODUITS:     int = 500
NB_MAGASINS:     int = 5
NB_FOURNISSEURS: int = 8

# Nombre moyen de ventes (tickets) par magasin par jour (jour ouvré normal)
VENTES_PAR_MAGASIN_PAR_JOUR: int = 500

# ─── Données de référence : Magasins ─────────────────────────────────────────
MAGASINS: list[dict] = [
    {"magasin_nk": "MAG-001", "nom": "RetailPlus Casablanca", "ville": "Casablanca", "region": "Casablanca-Settat",    "type": "Hypermarché", "surface_m2": 8_000},
    {"magasin_nk": "MAG-002", "nom": "RetailPlus Rabat",      "ville": "Rabat",      "region": "Rabat-Salé-Kénitra",  "type": "Supermarché", "surface_m2": 3_500},
    {"magasin_nk": "MAG-003", "nom": "RetailPlus Marrakech",  "ville": "Marrakech",  "region": "Marrakech-Safi",      "type": "Supermarché", "surface_m2": 3_200},
    {"magasin_nk": "MAG-004", "nom": "RetailPlus Fès",        "ville": "Fès",        "region": "Fès-Meknès",          "type": "Supermarché", "surface_m2": 2_800},
    {"magasin_nk": "MAG-005", "nom": "RetailPlus Tanger",     "ville": "Tanger",     "region": "Tanger-Tétouan-Al Hoceïma", "type": "Proximité",   "surface_m2":   800},
]

# ─── Données de référence : Fournisseurs ─────────────────────────────────────
FOURNISSEURS: list[dict] = [
    {"fournisseur_nk": "FOUR-001", "nom": "Centrale Laitière Maroc",   "categorie_principale": "Alimentaire",    "pays": "Maroc",    "delai_livraison_jours": 2},
    {"fournisseur_nk": "FOUR-002", "nom": "Cosumar Distribution",      "categorie_principale": "Alimentaire",    "pays": "Maroc",    "delai_livraison_jours": 3},
    {"fournisseur_nk": "FOUR-003", "nom": "Brasseries du Maroc",       "categorie_principale": "Boissons",       "pays": "Maroc",    "delai_livraison_jours": 2},
    {"fournisseur_nk": "FOUR-004", "nom": "Henkel Maghreb",            "categorie_principale": "Ménager",        "pays": "Maroc",    "delai_livraison_jours": 5},
    {"fournisseur_nk": "FOUR-005", "nom": "Samsung Electronics MENA",  "categorie_principale": "Électronique",   "pays": "Émirats",  "delai_livraison_jours": 14},
    {"fournisseur_nk": "FOUR-006", "nom": "Nestlé Maroc",              "categorie_principale": "Alimentaire",    "pays": "Maroc",    "delai_livraison_jours": 3},
    {"fournisseur_nk": "FOUR-007", "nom": "Ikea Logistics Morocco",    "categorie_principale": "Maison",         "pays": "Maroc",    "delai_livraison_jours": 7},
    {"fournisseur_nk": "FOUR-008", "nom": "Danone Dairy Morocco",      "categorie_principale": "Alimentaire",    "pays": "Maroc",    "delai_livraison_jours": 2},
]

# ─── Catalogue Produits : catégories, sous-catégories, fournisseurs ──────────
CATALOGUE_PRODUITS: list[dict] = [
    # (categorie, sous_categorie, nb_produits, fournisseur_nk, tva_pct)
    ("Alimentaire", "Céréales & Féculents",   40, "FOUR-002", 14),
    ("Alimentaire", "Viandes & Poissons",      40, "FOUR-001", 14),
    ("Alimentaire", "Produits laitiers",       40, "FOUR-008", 14),
    ("Alimentaire", "Fruits & Légumes",        40, "FOUR-006", 0),
    ("Alimentaire", "Conserves & Épices",      40, "FOUR-006", 14),
    ("Boissons",    "Eaux & Jus",              30, "FOUR-003", 14),
    ("Boissons",    "Sodas",                   25, "FOUR-003", 14),
    ("Boissons",    "Boissons chaudes",        25, "FOUR-002", 14),
    ("Ménager",     "Nettoyage",               30, "FOUR-004", 20),
    ("Ménager",     "Hygiène",                 25, "FOUR-004", 20),
    ("Ménager",     "Entretien",               25, "FOUR-004", 20),
    ("Électronique","Petit électroménager",    25, "FOUR-005", 20),
    ("Électronique","Audio & Vidéo",           25, "FOUR-005", 20),
    ("Électronique","Informatique",            20, "FOUR-005", 20),
    ("Maison",      "Cuisine",                 25, "FOUR-007", 20),
    ("Maison",      "Décoration",              25, "FOUR-007", 20),
    ("Maison",      "Linge de maison",         20, "FOUR-007", 20),
]

# ─── Saisonnalité — coefficients multiplicateurs ─────────────────────────────
# Simule les pics de vente (Ramadan ≈ mars, été, Noël, etc.)
COEFF_MOIS: dict[int, float] = {
    1: 0.80,   # Janvier  — mois creux post-fêtes
    2: 0.85,
    3: 1.25,   # Mars     — Ramadan 2024
    4: 1.30,   # Avril    — Ramadan + Aïd
    5: 0.90,
    6: 0.95,
    7: 1.10,   # Juillet  — vacances d'été
    8: 1.15,   # Août     — pic estival
    9: 0.90,
    10: 0.95,
    11: 1.00,
    12: 1.35,  # Décembre — fêtes de fin d'année
}

COEFF_JOUR_SEMAINE: dict[int, float] = {
    0: 0.90,   # Lundi
    1: 0.85,   # Mardi
    2: 0.90,   # Mercredi
    3: 0.95,   # Jeudi
    4: 1.15,   # Vendredi — grande journée shopping + prière
    5: 1.35,   # Samedi   — pic hebdomadaire
    6: 1.00,   # Dimanche
}

# ─── Segments clients ─────────────────────────────────────────────────────────
SEGMENTS_CLIENTS: dict[str, dict] = {
    "Premium":     {"panier_moyen_min": 500,  "frequence_mensuelle_min": 4,  "pct_population": 0.10},
    "Standard":    {"panier_moyen_min": 150,  "frequence_mensuelle_min": 1,  "pct_population": 0.50},
    "Occasionnel": {"panier_moyen_min": 0,    "frequence_mensuelle_min": 0,  "pct_population": 0.40},
}

# ─── Erreurs intentionnelles (pour tester le pipeline Silver) ────────────────
TAUX_ERREURS: dict[str, float] = {
    "doublons":            0.03,   # 3%  — lignes dupliquées
    "email_invalide":      0.05,   # 5%  — email client mal formé
    "quantite_negative":   0.02,   # 2%  — quantité ≤ 0
    "prix_negatif":        0.01,   # 1%  — prix de vente négatif
    "client_inexistant":   0.01,   # 1%  — client_nk fantôme
    "date_malformee":      0.01,   # 1%  — date au mauvais format
}

# ─── Chemins de sortie ────────────────────────────────────────────────────────
import os
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR  = os.path.join(BASE_DIR, "output", "csv")
LOG_DIR     = os.path.join(BASE_DIR, "output", "logs")
