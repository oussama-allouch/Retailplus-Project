# =============================================================================
# RetailPlus — main.py
# Point d'entrée principal du générateur de données.
# Lance tous les générateurs dans l'ordre correct et exporte les CSV.
# =============================================================================

import random
import logging
import os
import sys
import time
import io
import pandas as pd

# Ajout du répertoire courant au path Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Forcer UTF-8 sur stdout Windows (evite UnicodeEncodeError sur CP1252)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from config import RANDOM_SEED, OUTPUT_DIR, LOG_DIR

from generators.gen_magasins     import generate_magasins
from generators.gen_fournisseurs import generate_fournisseurs
from generators.gen_produits     import generate_produits
from generators.gen_clients      import generate_clients
from generators.gen_temps        import generate_temps
from generators.gen_stock        import generate_stock
from generators.gen_commandes    import generate_commandes
from generators.gen_ventes       import generate_ventes, update_segments_clients

# ─── Configuration du logging ─────────────────────────────────────────────────
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR,    exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(LOG_DIR, "generation.log"), encoding="utf-8"),
    ],
)
logger = logging.getLogger("RetailPlus.Generator")


def save_csv(df: pd.DataFrame, filename: str) -> None:
    """Exporte un DataFrame en CSV UTF-8 avec BOM (lisible dans Excel)."""
    path = os.path.join(OUTPUT_DIR, filename)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    size_mb = os.path.getsize(path) / (1024 * 1024)
    logger.info(f"  [OK] {filename:<40} {len(df):>10,} lignes  ({size_mb:.1f} MB)")


def run() -> None:
    """
    Orchestre la generation complete des donnees RetailPlus.
    Ordre imperatif :
        1. Referentiels (magasins, fournisseurs, produits, clients, temps)
        2. Transactions (stock, commandes, ventes, retours)
    """
    logger.info("=" * 65)
    logger.info("  RetailPlus -- Generateur de Donnees v1.0")
    logger.info(f"  Seed : {RANDOM_SEED}  |  Output : {OUTPUT_DIR}")
    logger.info("=" * 65)

    rng = random.Random(RANDOM_SEED)
    start_total = time.time()

    # ── 1. REFERENTIELS ──────────────────────────────────────────────────────
    logger.info("\n[1/3] Generation des REFERENTIELS")

    logger.info("  --> Magasins")
    df_magasins = generate_magasins()
    save_csv(df_magasins, "dim_magasin.csv")

    logger.info("  --> Fournisseurs")
    df_fournisseurs = generate_fournisseurs()
    save_csv(df_fournisseurs, "dim_fournisseur.csv")

    logger.info("  --> Produits (500)")
    df_produits = generate_produits(rng)
    save_csv(df_produits, "dim_produit.csv")

    logger.info("  --> Clients (10 000)")
    df_clients = generate_clients(rng)
    save_csv(df_clients, "dim_client_temp.csv")   # segment mis a jour apres ventes

    logger.info("  --> Dimension Temps (366 jours)")
    df_temps = generate_temps()
    save_csv(df_temps, "dim_temps.csv")

    # ── 2. TRANSACTIONS ───────────────────────────────────────────────────────
    logger.info("\n[2/3] Generation des TRANSACTIONS")

    logger.info("  --> Stock (snapshots mensuels)")
    df_stock = generate_stock(df_produits, rng)
    save_csv(df_stock, "fait_stock.csv")

    logger.info("  --> Commandes fournisseurs (~2 000)")
    df_commandes, df_lignes_cmd = generate_commandes(df_produits, df_fournisseurs, rng)
    save_csv(df_commandes,   "fait_commandes.csv")
    save_csv(df_lignes_cmd,  "fait_lignes_commandes.csv")

    logger.info("  --> Ventes (12 mois -- cela peut prendre quelques minutes...)")
    t0 = time.time()
    df_ventes, df_retours = generate_ventes(df_clients, df_produits, rng)
    logger.info(f"      Ventes generees en {time.time() - t0:.1f}s")
    save_csv(df_ventes,  "fait_ventes.csv")
    save_csv(df_retours, "fait_retours.csv")

    # ── 3. MISE A JOUR des segments clients ───────────────────────────────────
    logger.info("\n[3/3] Mise a jour des segments clients")
    df_clients_final = update_segments_clients(df_clients, df_ventes)
    save_csv(df_clients_final, "dim_client.csv")

    # Nettoyage du fichier temporaire
    temp_path = os.path.join(OUTPUT_DIR, "dim_client_temp.csv")
    if os.path.exists(temp_path):
        os.remove(temp_path)

    # ── 4. RAPPORT FINAL ─────────────────────────────────────────────────────
    duree_totale = time.time() - start_total
    logger.info("\n" + "=" * 65)
    logger.info("  RAPPORT DE GENERATION")
    logger.info("=" * 65)
    logger.info(f"  Magasins              : {len(df_magasins):>10,}")
    logger.info(f"  Fournisseurs          : {len(df_fournisseurs):>10,}")
    logger.info(f"  Produits              : {len(df_produits):>10,}")
    logger.info(f"  Clients               : {len(df_clients_final):>10,}")
    logger.info(f"  Jours (temps)         : {len(df_temps):>10,}")
    logger.info(f"  Snapshots stock       : {len(df_stock):>10,}")
    logger.info(f"  Commandes             : {len(df_commandes):>10,}")
    logger.info(f"  Lignes commandes      : {len(df_lignes_cmd):>10,}")
    logger.info(f"  Lignes ventes         : {len(df_ventes):>10,}")
    logger.info(f"  Retours               : {len(df_retours):>10,}")

    # Resume des erreurs injectees
    doublons     = len(df_ventes[df_ventes["vente_sk"] < 0])
    qte_neg      = len(df_ventes[df_ventes["quantite"] <= 0])
    prix_neg     = len(df_ventes[df_ventes["montant_ttc"] < 0])
    emails_inv   = len(df_clients_final[~df_clients_final["email_valide"]])

    logger.info("\n  Erreurs intentionnelles injectees :")
    logger.info(f"     Doublons ventes         : {doublons:>8,}")
    logger.info(f"     Quantites invalides     : {qte_neg:>8,}")
    logger.info(f"     Prix negatifs           : {prix_neg:>8,}")
    logger.info(f"     Emails invalides        : {emails_inv:>8,}")
    logger.info(f"\n  Duree totale : {duree_totale:.1f}s")
    logger.info("=" * 65)
    logger.info(f"  Tous les CSV sont dans : {OUTPUT_DIR}")
    logger.info("=" * 65)


if __name__ == "__main__":
    run()
