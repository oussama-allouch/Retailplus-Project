# =============================================================================
# RetailPlus — kafka_producer/producer.py
# Simulateur temps réel : publie des événements de vente/retour dans Kafka.
# En l'absence de Kafka (dev local), les événements sont loggés en JSON Lines.
# =============================================================================

import json
import random
import time
import logging
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MAGASINS, RANDOM_SEED, LOG_DIR

# ─── Configuration ────────────────────────────────────────────────────────────
KAFKA_BOOTSTRAP_SERVERS: str  = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC_VENTES:            str  = "retailplus.ventes"
TOPIC_RETOURS:           str  = "retailplus.retours"
INTERVALLE_SECONDES:     float = float(os.getenv("PRODUCER_INTERVAL_SEC", "0.5"))
TAUX_RETOUR_STREAM:      float = 0.05   # 5% des événements sont des retours

# ─── Logging ──────────────────────────────────────────────────────────────────
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(LOG_DIR, "kafka_producer.log"), encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def _build_vente_event(
    rng:         random.Random,
    client_nks:  list[str],
    produit_rows: list[dict],
    magasin_nks: list[str],
) -> dict:
    """Construit un événement de vente au format JSON Kafka."""
    mag_nk     = rng.choice(magasin_nks)
    client_nk  = rng.choice(client_nks)
    nb_lignes  = rng.randint(1, 6)
    produits   = rng.choices(produit_rows, k=nb_lignes)
    timestamp  = datetime.now(timezone.utc).isoformat()
    ticket_nk  = f"TKT-{mag_nk}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{rng.randint(1000,9999)}"

    lignes = []
    total_ttc = 0.0
    for prod in produits:
        qte      = rng.randint(1, 4)
        montant  = round(prod["prix_vente_ttc"] * qte, 2)
        total_ttc += montant
        lignes.append({
            "produit_nk":    prod["produit_nk"],
            "quantite":      qte,
            "prix_unitaire": prod["prix_vente_ttc"],
            "montant_ttc":   montant,
        })

    return {
        "event_id":           f"EVT-{rng.randint(100_000, 999_999)}",
        "event_type":         "VENTE",
        "timestamp":          timestamp,
        "ticket_nk":          ticket_nk,
        "magasin_nk":         mag_nk,
        "client_nk":          client_nk,
        "lignes":             lignes,
        "montant_total_ttc":  round(total_ttc, 2),
        "source":             "kafka-simulator",
    }


def _build_retour_event(rng: random.Random, magasin_nks: list[str], produit_rows: list[dict]) -> dict:
    """Construit un événement de retour."""
    prod = rng.choice(produit_rows)
    qte  = rng.randint(1, 2)
    return {
        "event_id":        f"EVT-RET-{rng.randint(100_000, 999_999)}",
        "event_type":      "RETOUR",
        "timestamp":       datetime.now(timezone.utc).isoformat(),
        "retour_nk":       f"RET-{rng.randint(1_000_000, 9_999_999)}",
        "magasin_nk":      rng.choice(magasin_nks),
        "produit_nk":      prod["produit_nk"],
        "quantite":        qte,
        "montant_ttc":     round(prod["prix_vente_ttc"] * qte, 2),
        "motif":           rng.choice(["Défectueux", "Changement d'avis", "Erreur commande"]),
        "source":          "kafka-simulator",
    }


def run_producer(df_clients, df_produits, use_kafka: bool = False) -> None:
    """
    Lance le simulateur.
    - use_kafka=True  → publie dans Kafka (nécessite kafka-python installé)
    - use_kafka=False → écrit dans un fichier JSON Lines (mode dev local)
    """
    rng          = random.Random(RANDOM_SEED)
    client_nks   = df_clients["client_nk"].tolist()
    produit_rows = df_produits[["produit_nk", "prix_vente_ttc"]].to_dict("records")
    magasin_nks  = [m["magasin_nk"] for m in MAGASINS]

    producer  = None
    sink_path = os.path.join(LOG_DIR, "kafka_events.jsonl")

    if use_kafka:
        try:
            from kafka import KafkaProducer
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
            )
            logger.info(f"✅ Connexion Kafka établie → {KAFKA_BOOTSTRAP_SERVERS}")
        except Exception as e:
            logger.warning(f"⚠️  Kafka non disponible ({e}). Bascule sur mode fichier.")
            use_kafka = False

    logger.info("🚀 Démarrage du simulateur RetailPlus — appuyez sur Ctrl+C pour arrêter")
    events_sent = 0

    try:
        with open(sink_path, "a", encoding="utf-8") as f_sink:
            while True:
                is_retour = rng.random() < TAUX_RETOUR_STREAM
                topic     = TOPIC_RETOURS if is_retour else TOPIC_VENTES
                event     = (
                    _build_retour_event(rng, magasin_nks, produit_rows)
                    if is_retour
                    else _build_vente_event(rng, client_nks, produit_rows, magasin_nks)
                )

                if use_kafka and producer:
                    producer.send(topic, event)
                else:
                    f_sink.write(json.dumps(event, ensure_ascii=False) + "\n")

                events_sent += 1
                if events_sent % 100 == 0:
                    logger.info(f"📊 {events_sent} événements envoyés vers [{topic}]")

                time.sleep(INTERVALLE_SECONDES)

    except KeyboardInterrupt:
        logger.info(f"⛔ Simulateur arrêté. Total événements : {events_sent}")
    finally:
        if producer:
            producer.close()
