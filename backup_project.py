# ==============================================================================
# RÈGLES MÉTIER PAIE & SOCIAL 2026 - OFFICIEL JANVIER 2026
# ==============================================================================

# -------------------------------------------------------------------------
# 1. CHIFFRES CLÉS & PLAFONDS (SOURCES : JO / BOSS / URSSAF)
# -------------------------------------------------------------------------
- id: PASS_2026
  keywords: ["pass", "pmss", "plafond", "securite", "sécurité", "sociale", "mensuel", "annuel"]
  valeurs:
    annuel: 48060
    mensuel: 4005
    horaire: 30
  derniere_maj: "Janvier 2026"
  source: "Arrêté du 22 décembre 2025 (JO du 23/12)"
  text: "Le Plafond Mensuel de la Sécurité Sociale (PMSS) 2026 est officiellement de 4 005 € (48 060 € par an)."

- id: SMIC_2026
  keywords: ["smic", "horaire", "salaire", "minimum", "mensuel", "brut", "taux"]
  valeurs:
    horaire: 12.02
    mensuel_35h: 1823.03
  derniere_maj: "Janvier 2026"
  source: "Décret 2026 (Révision possible selon inflation)"
  text: "Au 1er janvier 2026, le SMIC est de 12,02 € brut/heure, soit 1 823,03 € brut mensuel (35h)."

- id: MG_2026
  keywords: ["mg", "minimum", "garanti", "valeur", "repas"]
  valeurs:
    montant: 4.25
  derniere_maj: "Janvier 2026"
  source: "Barème URSSAF 2026"
  text: "Le Minimum Garanti (MG) est de 4,25 € au 1er janvier 2026."

# -------------------------------------------------------------------------
# 2. AVANTAGES EN NATURE & FRAIS
# -------------------------------------------------------------------------
- id: AVN_REPAS_2026
  keywords: ["repas", "nourriture", "avantage", "nature", "déjeuner", "dîner", "hcr"]
  valeurs:
    un_repas: 5.50
    deux_repas: 11.00
    hcr: 4.25
  derniere_maj: "Janvier 2026"
  source: "Barème URSSAF 2026"
  text: "L'avantage en nature nourriture est de 5,50 € par repas en 2026 (11,00 € pour deux repas). Pour le secteur HCR, la valeur est fixée à 1 MG soit 4,25 €."

- id: TICKET_RESTO_2026
  keywords: ["ticket", "resto", "titre", "restaurant", "cheque", "déjeuner", "patronale", "exonération"]
  valeurs:
    plafond_exonération: 7.32
  derniere_maj: "Janvier 2026"
  source: "Mise à jour URSSAF / BOSS Janvier 2026"
  text: "La limite d'exonération de la part patronale des titres-restaurant est fixée à 7,32 € en 2026 (pour une participation entre 50% et 60% de la valeur faciale)."

- id: FRAIS_TELETRAVAIL_2026
  keywords: ["teletravail", "télétravail", "indemnité", "frais", "allocation", "forfaitaire", "domicile", "jour"]
  valeurs:
    par_jour: 2.80
    limite_mensuelle_1j_semaine: 11.20
  derniere_maj: "Janvier 2026"
  source: "Barème URSSAF 2026"
  text: "L'indemnité de télétravail est exonérée à hauteur de 2,80 € par jour télétravaillé. La limite mensuelle s'apprécie en fonction du nombre de jours réels (ex: ~11,20 €/mois pour 1 jour/semaine)."

- id: AVN_VEHICULE_ELEC_2026
  keywords: ["vehicule", "véhicule", "electrique", "électrique", "abattement", "voiture", "recharge"]
  valeurs:
    plafond_abattement: 2003.00
  derniere_maj: "Janvier 2026"
  source: "URSSAF 2026 (Plafond indexé sur le PASS)"
  text: "L'abattement de 50% sur l'avantage en nature véhicule électrique (plafond de 2 003,00 €) est maintenu pour l'année 2026."

# -------------------------------------------------------------------------
# 3. STAGES, APPRENTISSAGE & SAISIES
# -------------------------------------------------------------------------
- id: GRATIFICATION_STAGE_2026
  keywords: ["stage", "stagiaire", "gratification", "minimale", "indemnité", "heure"]
  valeurs:
    taux_horaire: 4.50
  derniere_maj: "Janvier 2026"
  source: "Service-Public 2026 (15% du plafond horaire SS)"
  text: "La gratification minimale des stagiaires est de 4,50 € par heure au 1er janvier 2026 (soit 15% du plafond horaire de la sécurité sociale)."

- id: EXONERATION_APPRENTI_2026
  keywords: ["apprenti", "apprentissage", "cotisations", "exonération", "plafond", "79%", "seuil"]
  derniere_maj: "Janvier 2026"
  source: "LFSS 2026 / BOSS"
  text: "VÉRITÉ SYSTÈME 2026 : Le plafond d'exonération des cotisations salariales pour les apprentis est de 79% du SMIC. Toute mention de 50% issue d'articles anciens est obsolète."

- id: SBI_2026
  keywords: ["sbi", "solde", "bancaire", "insaisissable", "saisie", "salaire", "compte", "saisi"]
  valeurs:
    montant: 645.50
  derniere_maj: "Janvier 2026"
  source: "Barème Saisie 2026"
  text: "Le Solde Bancaire Insaisissable (SBI) est fixé à 645,50 € pour l'année 2026."

# -------------------------------------------------------------------------
# 4. FRAIS DE SANTÉ (MUTUELLE) & PRÉVOYANCE
# -------------------------------------------------------------------------
- id: HCR_SANTE_2026
  keywords: ["hcr", "mutuelle", "sante", "santé", "frais", "cotisation"]
  valeurs:
    cotisation_base: 52.00
  derniere_maj: "Janvier 2026"
  source: "Avenant HCR 2026"
  text: "La cotisation de base Mutuelle HCR (Frais de santé) est de 52,00 € au 1er janvier 2026, financée à 50% par l'employeur."

# -------------------------------------------------------------------------
# 5. RUPTURE DU CONTRAT & INDEMNITÉS
# -------------------------------------------------------------------------
- id: INDEMNITE_LICENCIEMENT_2026
  keywords: ["licenciement", "indemnite", "indemnité", "legale", "légale", "calcul", "rupture", "contrat", "fin"]
  valeurs:
    taux_base: "1/4 de mois par an"
  derniere_maj: "Janvier 2026"
  source: "Code du Travail 2026"
  text: "L'indemnité légale de licenciement est calculée sur la base de 1/4 de mois de salaire par an d'ancienneté jusqu'à 10 ans, et 1/3 de mois au-delà."

# -------------------------------------------------------------------------
# 6. LOGEMENT (AVANTAGE EN NATURE)
# -------------------------------------------------------------------------
- id: AVN_LOGEMENT_2026
  keywords: ["logement", "avantage", "nature", "loyer", "fonction", "frais"]
  valeurs:
    base: "Barème selon rémunération"
  derniere_maj: "Janvier 2026"
  source: "URSSAF 2026"
  text: "L'évaluation forfaitaire de l'avantage en nature logement s'effectue selon un barème de 8 tranches indexé sur le PASS."

# -------------------------------------------------------------------------
# 7. RÉDUCTION GÉNÉRALE & TRANSPORT
# -------------------------------------------------------------------------
- id: VERSEMENT_MOBILITE_2026
  keywords: ["versement", "mobilite", "mobilité", "transport", "taxe", "contribution"]
  derniere_maj: "Janvier 2026"
  source: "URSSAF (Révision semestrielle : Janvier / Juillet)"
  text: "Le Versement Mobilité est dû par les employeurs de 11 salariés et plus. Les taux sont mis à jour au 1er janvier et au 1er juillet."

- id: REDUCTION_GENERALE_2026
  keywords: ["reduction", "réduction", "generale", "générale", "fillon", "bas", "salaires", "smic", "coefficient", "t"]
  valeurs:
    T_moins_50: 0.3194
    T_plus_50: 0.3154
    smic_annuel: 21876.36
  derniere_maj: "Janvier 2026"
  source: "Décret 2026 / Code de la Sécurité Sociale"
  text: "Le coefficient T de la Réduction Générale (Fillon) dépend de l'effectif. Pour 2026, la valeur maximale est de 0,3194 (entreprises < 50 salariés) et de 0,3154 (entreprises ≥ 50 salariés, soumises au FNAL 0,50%)."