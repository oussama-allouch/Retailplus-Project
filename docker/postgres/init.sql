-- =============================================================================
-- RetailPlus — init.sql
-- Script d'initialisation de la base de données PostgreSQL
-- Crée les schémas bronze, silver et gold, ainsi que leurs tables.
-- =============================================================================

-- ─── 1. CRÉATION DES SCHÉMAS ──────────────────────────────────────────────────
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

-- ─── 2. SCHÉMA BRONZE (DONNÉES BRUTES / RAW) ──────────────────────────────────
-- Ce schéma reçoit les données telles quelles, sans typage fort ni contraintes complexes.

CREATE TABLE IF NOT EXISTS bronze.dim_magasin (
    magasin_nk VARCHAR(50),
    nom VARCHAR(100),
    ville VARCHAR(100),
    region VARCHAR(100),
    type VARCHAR(50),
    surface_m2 VARCHAR(50),
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.dim_fournisseur (
    fournisseur_nk VARCHAR(50),
    nom VARCHAR(150),
    categorie_principale VARCHAR(100),
    pays VARCHAR(100),
    delai_livraison_jours VARCHAR(50),
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.dim_produit (
    produit_nk VARCHAR(50),
    nom VARCHAR(150),
    categorie VARCHAR(100),
    sous_categorie VARCHAR(100),
    fournisseur_nk VARCHAR(50),
    prix_achat_ht VARCHAR(50),
    prix_vente_ht VARCHAR(50),
    tva_pct VARCHAR(50),
    prix_vente_ttc VARCHAR(50),
    marge_brute_ht VARCHAR(50),
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.dim_client (
    client_nk VARCHAR(50),
    prenom VARCHAR(100),
    nom VARCHAR(100),
    email VARCHAR(200),
    telephone VARCHAR(50),
    ville VARCHAR(100),
    date_naissance VARCHAR(50),
    date_inscription VARCHAR(50),
    segment VARCHAR(50),
    email_valide VARCHAR(20),
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.dim_temps (
    temps_sk VARCHAR(50),
    date_complete VARCHAR(50),
    jour VARCHAR(20),
    jour_semaine_num VARCHAR(20),
    jour_semaine_nom VARCHAR(50),
    semaine_annee VARCHAR(20),
    mois_num VARCHAR(20),
    mois_nom VARCHAR(50),
    trimestre VARCHAR(20),
    semestre VARCHAR(20),
    annee VARCHAR(20),
    est_weekend VARCHAR(20),
    est_ferie VARCHAR(20),
    est_jour_ouvre VARCHAR(20),
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.fait_stock (
    date_snapshot VARCHAR(50),
    produit_nk VARCHAR(50),
    magasin_nk VARCHAR(50),
    quantite_en_stock VARCHAR(50),
    valeur_stock_ht VARCHAR(50),
    seuil_reapprovisionnement VARCHAR(50),
    en_rupture VARCHAR(20),
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.fait_commandes (
    commande_nk VARCHAR(50),
    fournisseur_nk VARCHAR(50),
    magasin_nk VARCHAR(50),
    date_commande VARCHAR(50),
    date_livraison_prev VARCHAR(50),
    statut VARCHAR(50),
    montant_total_ht VARCHAR(50),
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.fait_lignes_commandes (
    commande_nk VARCHAR(50),
    produit_nk VARCHAR(50),
    quantite_commandee VARCHAR(50),
    prix_unitaire_achat VARCHAR(50),
    montant_ligne_ht VARCHAR(50),
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.fait_ventes (
    ticket_nk VARCHAR(100),
    timestamp_vente VARCHAR(100),
    date_vente VARCHAR(50),
    magasin_nk VARCHAR(50),
    client_nk VARCHAR(50),
    produit_nk VARCHAR(50),
    quantite VARCHAR(50),
    prix_unitaire_ht VARCHAR(50),
    tva_pct VARCHAR(50),
    prix_unitaire_ttc VARCHAR(50),
    montant_ht VARCHAR(50),
    montant_ttc VARCHAR(50),
    marge_brute_unit VARCHAR(50),
    marge_brute_total VARCHAR(50),
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.fait_retours (
    retour_nk VARCHAR(50),
    ticket_nk VARCHAR(100),
    produit_nk VARCHAR(50),
    magasin_nk VARCHAR(50),
    client_nk VARCHAR(50),
    date_vente_originale VARCHAR(50),
    date_retour VARCHAR(50),
    quantite_retournee VARCHAR(50),
    montant_rembourse VARCHAR(50),
    motif VARCHAR(200),
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ─── 3. SCHÉMA SILVER (DONNÉES NETTOYÉES & VALIDÉES) ──────────────────────────
-- Tables typées, dédupliquées et nettoyées de leurs anomalies.

CREATE TABLE IF NOT EXISTS silver.dim_magasin (
    magasin_nk VARCHAR(50) PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    ville VARCHAR(100) NOT NULL,
    region VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    surface_m2 INT NOT NULL,
    cleaned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS silver.dim_fournisseur (
    fournisseur_nk VARCHAR(50) PRIMARY KEY,
    nom VARCHAR(150) NOT NULL,
    categorie_principale VARCHAR(100) NOT NULL,
    pays VARCHAR(100) NOT NULL,
    delai_livraison_jours INT NOT NULL,
    cleaned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS silver.dim_produit (
    produit_nk VARCHAR(50) PRIMARY KEY,
    nom VARCHAR(150) NOT NULL,
    categorie VARCHAR(100) NOT NULL,
    sous_categorie VARCHAR(100) NOT NULL,
    fournisseur_nk VARCHAR(50) NOT NULL,
    prix_achat_ht DECIMAL(12,2) NOT NULL,
    prix_vente_ht DECIMAL(12,2) NOT NULL,
    tva_pct DECIMAL(5,2) NOT NULL,
    prix_vente_ttc DECIMAL(12,2) NOT NULL,
    marge_brute_ht DECIMAL(12,2) NOT NULL,
    cleaned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS silver.dim_client (
    client_nk VARCHAR(50) PRIMARY KEY,
    prenom VARCHAR(100) NOT NULL,
    nom VARCHAR(100) NOT NULL,
    email VARCHAR(200), -- peut être mis à NULL si invalide
    telephone VARCHAR(50) NOT NULL,
    ville VARCHAR(100) NOT NULL,
    date_naissance DATE NOT NULL,
    date_inscription DATE NOT NULL,
    segment VARCHAR(50) NOT NULL,
    cleaned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS silver.dim_temps (
    temps_sk INT PRIMARY KEY,
    date_complete DATE NOT NULL,
    jour INT NOT NULL,
    jour_semaine_num INT NOT NULL,
    jour_semaine_nom VARCHAR(50) NOT NULL,
    semaine_annee INT NOT NULL,
    mois_num INT NOT NULL,
    mois_nom VARCHAR(50) NOT NULL,
    trimestre INT NOT NULL,
    semestre INT NOT NULL,
    annee INT NOT NULL,
    est_weekend BOOLEAN NOT NULL,
    est_ferie BOOLEAN NOT NULL,
    est_jour_ouvre BOOLEAN NOT NULL,
    cleaned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS silver.fait_stock (
    date_snapshot DATE NOT NULL,
    produit_nk VARCHAR(50) NOT NULL REFERENCES silver.dim_produit(produit_nk),
    magasin_nk VARCHAR(50) NOT NULL REFERENCES silver.dim_magasin(magasin_nk),
    quantite_en_stock INT NOT NULL,
    valeur_stock_ht DECIMAL(12,2) NOT NULL,
    seuil_reapprovisionnement INT NOT NULL,
    en_rupture BOOLEAN NOT NULL,
    cleaned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (date_snapshot, produit_nk, magasin_nk)
);

CREATE TABLE IF NOT EXISTS silver.fait_commandes (
    commande_nk VARCHAR(50) PRIMARY KEY,
    fournisseur_nk VARCHAR(50) NOT NULL REFERENCES silver.dim_fournisseur(fournisseur_nk),
    magasin_nk VARCHAR(50) NOT NULL REFERENCES silver.dim_magasin(magasin_nk),
    date_commande DATE NOT NULL,
    date_livraison_prev DATE NOT NULL,
    statut VARCHAR(50) NOT NULL,
    montant_total_ht DECIMAL(12,2) NOT NULL,
    cleaned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS silver.fait_lignes_commandes (
    commande_nk VARCHAR(50) NOT NULL REFERENCES silver.fait_commandes(commande_nk),
    produit_nk VARCHAR(50) NOT NULL REFERENCES silver.dim_produit(produit_nk),
    quantite_commandee INT NOT NULL,
    prix_unitaire_achat DECIMAL(12,2) NOT NULL,
    montant_ligne_ht DECIMAL(12,2) NOT NULL,
    cleaned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (commande_nk, produit_nk)
);

CREATE TABLE IF NOT EXISTS silver.fait_ventes (
    ticket_nk VARCHAR(100) NOT NULL,
    timestamp_vente TIMESTAMP NOT NULL,
    date_vente DATE NOT NULL,
    magasin_nk VARCHAR(50) NOT NULL REFERENCES silver.dim_magasin(magasin_nk),
    client_nk VARCHAR(50) REFERENCES silver.dim_client(client_nk),
    produit_nk VARCHAR(50) NOT NULL REFERENCES silver.dim_produit(produit_nk),
    quantite INT NOT NULL,
    prix_unitaire_ht DECIMAL(12,2) NOT NULL,
    tva_pct DECIMAL(5,2) NOT NULL,
    prix_unitaire_ttc DECIMAL(12,2) NOT NULL,
    montant_ht DECIMAL(12,2) NOT NULL,
    montant_ttc DECIMAL(12,2) NOT NULL,
    marge_brute_unit DECIMAL(12,2) NOT NULL,
    marge_brute_total DECIMAL(12,2) NOT NULL,
    cleaned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ticket_nk, produit_nk)
);

CREATE TABLE IF NOT EXISTS silver.fait_retours (
    retour_nk VARCHAR(50) PRIMARY KEY,
    ticket_nk VARCHAR(100) NOT NULL,
    produit_nk VARCHAR(50) NOT NULL REFERENCES silver.dim_produit(produit_nk),
    magasin_nk VARCHAR(50) NOT NULL REFERENCES silver.dim_magasin(magasin_nk),
    client_nk VARCHAR(50) REFERENCES silver.dim_client(client_nk),
    date_vente_originale DATE NOT NULL,
    date_retour DATE NOT NULL,
    quantite_retournee INT NOT NULL,
    montant_rembourse DECIMAL(12,2) NOT NULL,
    motif VARCHAR(200) NOT NULL,
    cleaned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des rejets pour la gouvernance de données
CREATE TABLE IF NOT EXISTS silver.rejected_records (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_data TEXT NOT NULL,
    reason VARCHAR(255) NOT NULL,
    rejected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ─── 4. SCHÉMA GOLD (ENTREPÔT DE DONNÉES EN ÉTOILE / DATA WAREHOUSE) ─────────
-- Clés de substitution (Surrogate Keys) et modélisation dimensionnelle optimale pour la BI.

CREATE TABLE IF NOT EXISTS gold.dim_magasin (
    magasin_sk SERIAL PRIMARY KEY,
    magasin_nk VARCHAR(50) UNIQUE NOT NULL,
    nom VARCHAR(100) NOT NULL,
    ville VARCHAR(100) NOT NULL,
    region VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    surface_m2 INT NOT NULL,
    est_actif BOOLEAN NOT NULL DEFAULT TRUE,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS gold.dim_fournisseur (
    fournisseur_sk SERIAL PRIMARY KEY,
    fournisseur_nk VARCHAR(50) UNIQUE NOT NULL,
    nom VARCHAR(150) NOT NULL,
    categorie_principale VARCHAR(100) NOT NULL,
    pays VARCHAR(100) NOT NULL,
    delai_livraison_jours INT NOT NULL,
    est_actif BOOLEAN NOT NULL DEFAULT TRUE,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS gold.dim_produit (
    produit_sk SERIAL PRIMARY KEY,
    produit_nk VARCHAR(50) UNIQUE NOT NULL,
    nom VARCHAR(150) NOT NULL,
    categorie VARCHAR(100) NOT NULL,
    sous_categorie VARCHAR(100) NOT NULL,
    fournisseur_sk INT REFERENCES gold.dim_fournisseur(fournisseur_sk),
    prix_achat_ht DECIMAL(12,2) NOT NULL,
    prix_vente_ht DECIMAL(12,2) NOT NULL,
    tva_pct DECIMAL(5,2) NOT NULL,
    prix_vente_ttc DECIMAL(12,2) NOT NULL,
    marge_brute_ht DECIMAL(12,2) NOT NULL,
    est_actif BOOLEAN NOT NULL DEFAULT TRUE,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS gold.dim_client (
    client_sk SERIAL PRIMARY KEY,
    client_nk VARCHAR(50) UNIQUE NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    nom VARCHAR(100) NOT NULL,
    email VARCHAR(200),
    telephone VARCHAR(50) NOT NULL,
    ville VARCHAR(100) NOT NULL,
    date_naissance DATE NOT NULL,
    date_inscription DATE NOT NULL,
    segment VARCHAR(50) NOT NULL,
    est_actif BOOLEAN NOT NULL DEFAULT TRUE,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Utilise la clé sk de type AAAAMMJJ pour de meilleures jointures temporelles
CREATE TABLE IF NOT EXISTS gold.dim_temps (
    temps_sk INT PRIMARY KEY,
    date_complete DATE NOT NULL,
    jour INT NOT NULL,
    jour_semaine_num INT NOT NULL,
    jour_semaine_nom VARCHAR(50) NOT NULL,
    semaine_annee INT NOT NULL,
    mois_num INT NOT NULL,
    mois_nom VARCHAR(50) NOT NULL,
    trimestre INT NOT NULL,
    semestre INT NOT NULL,
    annee INT NOT NULL,
    est_weekend BOOLEAN NOT NULL,
    est_ferie BOOLEAN NOT NULL,
    est_jour_ouvre BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS gold.fait_stock (
    stock_sk SERIAL PRIMARY KEY,
    date_snapshot_sk INT NOT NULL REFERENCES gold.dim_temps(temps_sk),
    produit_sk INT NOT NULL REFERENCES gold.dim_produit(produit_sk),
    magasin_sk INT NOT NULL REFERENCES gold.dim_magasin(magasin_sk),
    quantite_en_stock INT NOT NULL,
    valeur_stock_ht DECIMAL(12,2) NOT NULL,
    seuil_reapprovisionnement INT NOT NULL,
    en_rupture BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS gold.fait_commandes (
    commande_sk SERIAL PRIMARY KEY,
    commande_nk VARCHAR(50) UNIQUE NOT NULL,
    fournisseur_sk INT NOT NULL REFERENCES gold.dim_fournisseur(fournisseur_sk),
    magasin_sk INT NOT NULL REFERENCES gold.dim_magasin(magasin_sk),
    date_commande_sk INT NOT NULL REFERENCES gold.dim_temps(temps_sk),
    date_livraison_prev_sk INT NOT NULL REFERENCES gold.dim_temps(temps_sk),
    statut VARCHAR(50) NOT NULL,
    montant_total_ht DECIMAL(12,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS gold.fait_lignes_commandes (
    ligne_commande_sk SERIAL PRIMARY KEY,
    commande_sk INT NOT NULL REFERENCES gold.fait_commandes(commande_sk) ON DELETE CASCADE,
    produit_sk INT NOT NULL REFERENCES gold.dim_produit(produit_sk),
    quantite_commandee INT NOT NULL,
    prix_unitaire_achat DECIMAL(12,2) NOT NULL,
    montant_ligne_ht DECIMAL(12,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS gold.fait_ventes (
    vente_sk SERIAL PRIMARY KEY,
    ticket_nk VARCHAR(100) NOT NULL,
    timestamp_vente TIMESTAMP NOT NULL,
    date_sk INT NOT NULL REFERENCES gold.dim_temps(temps_sk),
    magasin_sk INT NOT NULL REFERENCES gold.dim_magasin(magasin_sk),
    client_sk INT REFERENCES gold.dim_client(client_sk),
    produit_sk INT NOT NULL REFERENCES gold.dim_produit(produit_sk),
    quantite INT NOT NULL,
    prix_unitaire_ht DECIMAL(12,2) NOT NULL,
    tva_pct DECIMAL(5,2) NOT NULL,
    prix_unitaire_ttc DECIMAL(12,2) NOT NULL,
    montant_ht DECIMAL(12,2) NOT NULL,
    montant_ttc DECIMAL(12,2) NOT NULL,
    marge_brute_unit DECIMAL(12,2) NOT NULL,
    marge_brute_total DECIMAL(12,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS gold.fait_retours (
    retour_sk SERIAL PRIMARY KEY,
    retour_nk VARCHAR(50) UNIQUE NOT NULL,
    ticket_nk VARCHAR(100) NOT NULL,
    produit_sk INT NOT NULL REFERENCES gold.dim_produit(produit_sk),
    magasin_sk INT NOT NULL REFERENCES gold.dim_magasin(magasin_sk),
    client_sk INT REFERENCES gold.dim_client(client_sk),
    date_vente_originale_sk INT NOT NULL REFERENCES gold.dim_temps(temps_sk),
    date_retour_sk INT NOT NULL REFERENCES gold.dim_temps(temps_sk),
    quantite_retournee INT NOT NULL,
    montant_rembourse DECIMAL(12,2) NOT NULL,
    motif VARCHAR(200) NOT NULL
);

-- ─── 5. INDEXATION POUR L'OPTIMISATION DES REQUÊTES BI ────────────────────────
CREATE INDEX IF NOT EXISTS idx_gold_ventes_date ON gold.fait_ventes(date_sk);
CREATE INDEX IF NOT EXISTS idx_gold_ventes_produit ON gold.fait_ventes(produit_sk);
CREATE INDEX IF NOT EXISTS idx_gold_ventes_magasin ON gold.fait_ventes(magasin_sk);
CREATE INDEX IF NOT EXISTS idx_gold_ventes_client ON gold.fait_ventes(client_sk);

CREATE INDEX IF NOT EXISTS idx_gold_stock_date ON gold.fait_stock(date_snapshot_sk);
CREATE INDEX IF NOT EXISTS idx_gold_stock_produit ON gold.fait_stock(produit_sk);
CREATE INDEX IF NOT EXISTS idx_gold_stock_magasin ON gold.fait_stock(magasin_sk);
