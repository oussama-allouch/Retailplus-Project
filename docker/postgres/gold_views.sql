-- =============================================================================
-- RetailPlus — docker/postgres/gold_views.sql
-- Vues SQL Analytiques et Décisionnelles sur le Schéma Gold (Star Schema)
-- =============================================================================

-- ─── 1. Vue KPI Globaux (Exécutif) ───────────────────────────────────────────
CREATE OR REPLACE VIEW gold.vue_kpis_globaux AS
SELECT
    COUNT(DISTINCT v.vente_sk)                  AS total_transactions,
    SUM(v.quantite)                             AS total_articles_vendus,
    ROUND(SUM(v.montant_ttc)::numeric, 2)       AS chiffre_affaires_ttc,
    ROUND(SUM(v.montant_ht)::numeric, 2)        AS chiffre_affaires_ht,
    ROUND(SUM(v.marge_brute_total)::numeric, 2) AS marge_brute_totale,
    ROUND((SUM(v.marge_brute_total) / NULLIF(SUM(v.montant_ht), 0) * 100)::numeric, 2) AS taux_marge_pct,
    ROUND((SUM(v.montant_ttc) / NULLIF(COUNT(DISTINCT v.vente_sk), 0))::numeric, 2) AS panier_moyen_ttc,
    COUNT(DISTINCT v.client_sk)                 AS clients_actifs,
    COUNT(DISTINCT v.magasin_sk)                AS total_magasins,
    COUNT(DISTINCT v.produit_sk)                AS total_produits_vendus
FROM gold.fait_ventes v;


-- ─── 2. Vue Évolution Mensuelle des Ventes ──────────────────────────────────
CREATE OR REPLACE VIEW gold.vue_ventes_mensuelles AS
SELECT
    t.annee,
    t.mois_num,
    t.mois_nom,
    t.trimestre,
    m.magasin_sk,
    m.nom                                       AS magasin_nom,
    m.ville                                     AS magasin_ville,
    COUNT(DISTINCT v.vente_sk)                  AS total_transactions,
    SUM(v.quantite)                             AS articles_vendus,
    ROUND(SUM(v.montant_ttc)::numeric, 2)       AS chiffre_affaires_ttc,
    ROUND(SUM(v.montant_ht)::numeric, 2)        AS chiffre_affaires_ht,
    ROUND(SUM(v.marge_brute_total)::numeric, 2) AS marge_brute_totale,
    ROUND((SUM(v.montant_ttc) / NULLIF(COUNT(DISTINCT v.vente_sk), 0))::numeric, 2) AS panier_moyen
FROM gold.fait_ventes v
JOIN gold.dim_temps t   ON v.date_sk = t.temps_sk
JOIN gold.dim_magasin m ON v.magasin_sk = m.magasin_sk
GROUP BY t.annee, t.mois_num, t.mois_nom, t.trimestre, m.magasin_sk, m.nom, m.ville
ORDER BY t.annee, t.mois_num, m.nom;


-- ─── 3. Vue Performance par Magasin & Ville ─────────────────────────────────
CREATE OR REPLACE VIEW gold.vue_performance_magasins AS
SELECT
    m.magasin_sk,
    m.magasin_nk,
    m.nom                                       AS magasin_nom,
    m.ville,
    m.region,
    m.surface_m2,
    COUNT(DISTINCT v.vente_sk)                  AS total_transactions,
    SUM(v.quantite)                             AS total_articles_vendus,
    ROUND(SUM(v.montant_ttc)::numeric, 2)       AS chiffre_affaires_ttc,
    ROUND(SUM(v.montant_ht)::numeric, 2)        AS chiffre_affaires_ht,
    ROUND(SUM(v.marge_brute_total)::numeric, 2) AS marge_brute_totale,
    ROUND((SUM(v.marge_brute_total) / NULLIF(SUM(v.montant_ht), 0) * 100)::numeric, 2) AS taux_marge_pct,
    ROUND((SUM(v.montant_ttc) / NULLIF(COUNT(DISTINCT v.vente_sk), 0))::numeric, 2) AS panier_moyen_ttc,
    ROUND((SUM(v.montant_ttc) / NULLIF(m.surface_m2, 0))::numeric, 2) AS ca_par_m2,
    COALESCE(r.total_retours, 0)                AS total_retours,
    COALESCE(r.montant_retours_rembourse, 0)   AS montant_retours_rembourse,
    ROUND((COALESCE(r.total_retours, 0)::numeric / NULLIF(COUNT(DISTINCT v.vente_sk), 0) * 100), 2) AS taux_retour_pct
FROM gold.dim_magasin m
LEFT JOIN gold.fait_ventes v ON m.magasin_sk = v.magasin_sk
LEFT JOIN (
    SELECT
        magasin_sk,
        COUNT(retour_sk) AS total_retours,
        ROUND(SUM(montant_rembourse)::numeric, 2) AS montant_retours_rembourse
    FROM gold.fait_retours
    GROUP BY magasin_sk
) r ON m.magasin_sk = r.magasin_sk
GROUP BY m.magasin_sk, m.magasin_nk, m.nom, m.ville, m.region, m.surface_m2, r.total_retours, r.montant_retours_rembourse
ORDER BY chiffre_affaires_ttc DESC;


-- ─── 4. Vue Performance par Catégorie et Top Produits ───────────────────────
CREATE OR REPLACE VIEW gold.vue_performance_produits AS
SELECT
    p.produit_sk,
    p.produit_nk,
    p.nom                                       AS produit_nom,
    p.categorie,
    p.sous_categorie,
    p.prix_vente_ttc,
    p.marge_brute_ht                            AS marge_unitaire,
    f.nom                                       AS fournisseur_nom,
    COUNT(DISTINCT v.vente_sk)                  AS total_transactions,
    SUM(v.quantite)                             AS total_quantite_vendue,
    ROUND(SUM(v.montant_ttc)::numeric, 2)       AS chiffre_affaires_ttc,
    ROUND(SUM(v.marge_brute_total)::numeric, 2) AS marge_brute_totale,
    ROUND((SUM(v.marge_brute_total) / NULLIF(SUM(v.montant_ht), 0) * 100)::numeric, 2) AS taux_marge_pct
FROM gold.dim_produit p
LEFT JOIN gold.dim_fournisseur f ON p.fournisseur_sk = f.fournisseur_sk
LEFT JOIN gold.fait_ventes v     ON p.produit_sk = v.produit_sk
GROUP BY p.produit_sk, p.produit_nk, p.nom, p.categorie, p.sous_categorie, p.prix_vente_ttc, p.marge_brute_ht, f.nom
ORDER BY chiffre_affaires_ttc DESC NULLS LAST;


-- ─── 5. Vue Segmentation et Comportement Clients ────────────────────────────
CREATE OR REPLACE VIEW gold.vue_segmentation_clients AS
SELECT
    c.client_sk,
    c.client_nk,
    c.nom,
    c.prenom,
    c.ville                                     AS client_ville,
    c.segment,
    COUNT(DISTINCT v.vente_sk)                  AS nb_achats,
    COALESCE(SUM(v.quantite), 0)                AS total_articles_achetes,
    ROUND(COALESCE(SUM(v.montant_ttc), 0)::numeric, 2) AS depense_totale_ttc,
    ROUND((COALESCE(SUM(v.montant_ttc), 0) / NULLIF(COUNT(DISTINCT v.vente_sk), 0))::numeric, 2) AS panier_moyen,
    ROUND(COALESCE(SUM(v.marge_brute_total), 0)::numeric, 2) AS marge_totale_generee,
    MIN(t.date_complete)                        AS date_premier_achat,
    MAX(t.date_complete)                        AS date_dernier_achat
FROM gold.dim_client c
LEFT JOIN gold.fait_ventes v ON c.client_sk = v.client_sk
LEFT JOIN gold.dim_temps t   ON v.date_sk = t.temps_sk
GROUP BY c.client_sk, c.client_nk, c.nom, c.prenom, c.ville, c.segment
ORDER BY depense_totale_ttc DESC NULLS LAST;


-- ─── 6. Vue Gestion des Stocks et Logistique ────────────────────────────────
CREATE OR REPLACE VIEW gold.vue_gestion_stocks AS
SELECT
    s.produit_sk,
    p.nom                                       AS produit_nom,
    p.categorie,
    p.sous_categorie,
    m.nom                                       AS magasin_nom,
    m.ville                                     AS magasin_ville,
    f.nom                                       AS fournisseur_nom,
    f.delai_livraison_jours,
    AVG(s.quantite_en_stock)                    AS stock_moyen,
    ROUND(AVG(s.valeur_stock_ht)::numeric, 2)   AS valeur_stock_moyenne_ht,
    COUNT(CASE WHEN s.en_rupture THEN 1 END)    AS nb_occurrences_rupture,
    ROUND((COUNT(CASE WHEN s.en_rupture THEN 1 END)::numeric / NULLIF(COUNT(*), 0) * 100), 2) AS taux_rupture_pct
FROM gold.fait_stock s
JOIN gold.dim_produit p     ON s.produit_sk = p.produit_sk
JOIN gold.dim_magasin m     ON s.magasin_sk = m.magasin_sk
LEFT JOIN gold.dim_fournisseur f ON p.fournisseur_sk = f.fournisseur_sk
GROUP BY s.produit_sk, p.nom, p.categorie, p.sous_categorie, m.nom, m.ville, f.nom, f.delai_livraison_jours
ORDER BY nb_occurrences_rupture DESC;


-- ─── 7. Vue Analyse des Retours & Motifs ────────────────────────────────────
CREATE OR REPLACE VIEW gold.vue_analyse_retours AS
SELECT
    r.motif,
    p.categorie                                 AS categorie_produit,
    m.nom                                       AS magasin_nom,
    m.ville                                     AS magasin_ville,
    COUNT(r.retour_sk)                          AS total_retours,
    SUM(r.quantite_retournee)                   AS total_quantite_retournee,
    ROUND(SUM(r.montant_rembourse)::numeric, 2) AS total_montant_rembourse
FROM gold.fait_retours r
JOIN gold.dim_produit p ON r.produit_sk = p.produit_sk
JOIN gold.dim_magasin m ON r.magasin_sk = m.magasin_sk
GROUP BY r.motif, p.categorie, m.nom, m.ville
ORDER BY total_retours DESC;
