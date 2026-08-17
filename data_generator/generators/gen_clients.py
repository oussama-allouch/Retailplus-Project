# =============================================================================
# RetailPlus — generators/gen_clients.py
# Génère la dimension Client (10 000 clients marocains réalistes).
# =============================================================================

import random
import re
import pandas as pd
from faker import Faker
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RANDOM_SEED, NB_CLIENTS, TAUX_ERREURS

# Faker configuré pour générer des noms français (proxy pour noms marocains)
fake_fr = Faker("fr_FR")
fake_fr.seed_instance(RANDOM_SEED)

VILLES_CLIENTS: list[str] = [
    "Casablanca", "Rabat", "Marrakech", "Fès", "Tanger",
    "Agadir",     "Meknès",  "Oujda",  "Kénitra", "Tétouan",
    "El Jadida",  "Béni Mellal", "Nador", "Safi", "Laâyoune",
]

# Distribution des villes (les grandes villes ont plus de clients)
POIDS_VILLES: list[float] = [
    0.25, 0.15, 0.10, 0.08, 0.08,
    0.06, 0.05, 0.05, 0.04, 0.04,
    0.03, 0.02, 0.02, 0.02, 0.01,
]

# Préfixes téléphoniques marocains
PREFIXES_TEL: list[str] = ["06", "07"]


def _generate_phone(rng: random.Random) -> str:
    prefix = rng.choice(PREFIXES_TEL)
    number = rng.randint(10_000_000, 99_999_999)
    return f"+212 {prefix[1]}{number}"


def _generate_email(prenom: str, nom: str, client_nk: str, rng: random.Random, inject_error: bool) -> str:
    """Génère un email. inject_error=True → email intentionnellement invalide."""
    domains = ["gmail.com", "yahoo.fr", "hotmail.com", "menara.ma", "outlook.com"]
    slug    = f"{prenom.lower().replace(' ', '')}.{nom.lower().replace(' ', '')}"
    slug    = re.sub(r"[^a-z0-9.]", "", slug)
    email   = f"{slug}{rng.randint(1, 999)}@{rng.choice(domains)}"

    if inject_error:
        # Erreur : suppression du '@' → email invalide pour tester le pipeline Silver
        email = email.replace("@", "")

    return email


def generate_clients(rng: random.Random) -> pd.DataFrame:
    """
    Génère NB_CLIENTS clients.
    - Noms/prénoms : Faker fr_FR (noms réalistes)
    - Villes      : distribution pondérée vers les grandes villes
    - 5% d'emails invalides injectés intentionnellement
    - Le segment (Premium/Standard/Occasionnel) sera calculé APRÈS les ventes
    """
    clients: list[dict] = []

    for i in range(1, NB_CLIENTS + 1):
        prenom     = fake_fr.first_name()
        nom        = fake_fr.last_name()
        client_nk  = f"CLI-{i:05d}"

        inject_email_error = rng.random() < TAUX_ERREURS["email_invalide"]

        clients.append({
            "client_sk":        i,
            "client_nk":        client_nk,
            "prenom":           prenom,
            "nom":              nom,
            "email":            _generate_email(prenom, nom, client_nk, rng, inject_email_error),
            "telephone":        _generate_phone(rng),
            "ville":            rng.choices(VILLES_CLIENTS, weights=POIDS_VILLES, k=1)[0],
            "date_naissance":   str(fake_fr.date_of_birth(minimum_age=18, maximum_age=75)),
            "date_inscription": str(fake_fr.date_between(start_date="-5y", end_date="-1y")),
            "segment":          "À calculer",   # rempli après gen_ventes
            "email_valide":     not inject_email_error,
        })

    return pd.DataFrame(clients)
