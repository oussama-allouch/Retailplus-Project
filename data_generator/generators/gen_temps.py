# =============================================================================
# RetailPlus — generators/gen_temps.py
# Génère la dimension Temps (1 ligne par jour de la période historique).
# =============================================================================

import pandas as pd
from datetime import date, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATE_DEBUT, DATE_FIN

# Jours fériés marocains 2024 (approximatifs)
JOURS_FERIES_MAROC_2024: set[date] = {
    date(2024, 1, 1),   # Nouvel An
    date(2024, 1, 11),  # Manifeste de l'Indépendance
    date(2024, 4, 10),  # Aïd Al-Fitr (Ramadan)
    date(2024, 4, 11),  # Aïd Al-Fitr (2ème jour)
    date(2024, 5, 1),   # Fête du Travail
    date(2024, 6, 17),  # Aïd Al-Adha
    date(2024, 7, 30),  # Fête du Trône
    date(2024, 8, 14),  # Allégeance des provinces
    date(2024, 8, 20),  # Révolution du Roi et du Peuple
    date(2024, 8, 21),  # Fête de la Jeunesse
    date(2024, 11, 6),  # Marche Verte
    date(2024, 11, 18), # Fête de l'Indépendance
}

NOMS_MOIS_FR: dict[int, str] = {
    1: "Janvier", 2: "Février",  3: "Mars",      4: "Avril",
    5: "Mai",     6: "Juin",     7: "Juillet",   8: "Août",
    9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre",
}

NOMS_JOURS_FR: dict[int, str] = {
    0: "Lundi", 1: "Mardi", 2: "Mercredi", 3: "Jeudi",
    4: "Vendredi", 5: "Samedi", 6: "Dimanche",
}


def generate_temps() -> pd.DataFrame:
    """
    Retourne le DataFrame dim_temps avec une ligne par jour.
    Enrichi avec les métadonnées temporelles utilisées dans les KPIs :
    - Numéro de semaine, trimestre, semestre
    - Indicateur weekend / jour férié
    - Libellés en français
    """
    rows: list[dict] = []
    current: date   = DATE_DEBUT
    sk: int         = 1

    while current <= DATE_FIN:
        rows.append({
            "temps_sk":          int(current.strftime("%Y%m%d")),   # clé naturelle YYYYMMDD
            "date_complete":     str(current),
            "jour":              current.day,
            "jour_semaine_num":  current.weekday(),                 # 0=Lundi … 6=Dimanche
            "jour_semaine_nom":  NOMS_JOURS_FR[current.weekday()],
            "semaine_annee":     int(current.strftime("%V")),
            "mois_num":          current.month,
            "mois_nom":          NOMS_MOIS_FR[current.month],
            "trimestre":         (current.month - 1) // 3 + 1,
            "semestre":          1 if current.month <= 6 else 2,
            "annee":             current.year,
            "est_weekend":       current.weekday() >= 5,
            "est_ferie":         current in JOURS_FERIES_MAROC_2024,
            "est_jour_ouvre":    current.weekday() < 5 and current not in JOURS_FERIES_MAROC_2024,
        })
        current += timedelta(days=1)
        sk      += 1

    df = pd.DataFrame(rows)
    return df
