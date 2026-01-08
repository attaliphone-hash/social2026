import os

# Configuration du dossier de sortie
output_dir = "data_clean"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# BASE DE CONNAISSANCES ULTIME (BOSS + CODES + JURISPRUDENCE + 2026)
knowledge_base = {
    # --- 1. RÉFÉRENCES ET CHIFFRES CLÉS 2026 (MÉMO 2026 & BOSS) ---
    "REF_2026_PASS_SMIC.txt": "VALEURS 2026 : PASS Annuel 48060€, Mensuel 4005€, Horaire 30€. SMIC Horaire 12.02€, Mensuel (151.67h) 1823.03€. Minimum Garanti (MG) : 4.25€.",
    "REF_2026_ALLEGEMENTS_T.txt": "RÉDUCTION GÉNÉRALE 2026 (Paramètre T) : 0.3206 (Entreprises < 50 sal) et 0.3246 (Entreprises >= 50 sal). SMIC annuel de référence : 21 876,40€.",
    "REF_2026_FRAIS_REPAS.txt": "FRAIS PRO 2026 : Restaurant (déplacement) 10.10€, Panier/Indemnité repas 7.30€. Titre-Restaurant (part patronale max exo) : 7.33€.",
    "REF_2026_GRAND_DEPLACEMENT.txt": "GRAND DÉPLACEMENT 2026 : Logement + Petit déj : 73.80€ (Paris/RP) et 54.40€ (Province).",
    "REF_2025_BAREMES_STAGIAIRES.txt": "STAGIAIRES 2025/2026 : Franchise de cotisations à 4.35€/heure (15% du plafond horaire de 29€).",
    "REF_2025_BAREMES_HS_SALARIAL.txt": "HEURES SUPP : Taux réduction salariale max 11.31%. Exonération fiscale plafonnée à 7500€ net/an.",

    # --- 2. DOCTRINE ET RÈGLES DE CALCUL (BOSS) ---
    "DOC_BOSS_ASSIETTE_CSG.txt": "ASSIETTE CSG/CRDS : 98.25% du brut (abattement 1.75% plafonné à 4 PASS). 100% pour l'épargne salariale.",
    "DOC_BOSS_AVN_VEHICULE_ELEC.txt": "AVANTAGE VÉHICULE ÉLECTRIQUE : Abattement de 70% sur l'avantage global, plafonné à 4582€/an. Prise en charge électricité non soumise.",
    "DOC_BOSS_FRAIS_TELETRAVAIL.txt": "TÉLÉTRAVAIL : Exonération 2.70€/jour (max 59.40€/mois) ou 10.90€/mois pour 1 jour/semaine.",
    "DOC_BOSS_EFFECTIF_CALCUL.txt": "EFFECTIF MOYEN ANNUEL (EMA) : Moyenne des effectifs au dernier jour de chaque mois de l'année N-1. Proratisation temps partiel.",
    "DOC_BOSS_RUPTURE_CONV.txt": "RUPTURE CONVENTIONNELLE : Contribution patronale spécifique de 30% sur la part exonérée. Exonération limite 2 PASS.",
    "DOC_BOSS_MNS_CALCUL.txt": "MONTANT NET SOCIAL : Agrégat obligatoire. Calcul = Sommes brutes moins cotisations sociales salariales obligatoires.",
    "DOC_BOSS_PSC_SANTE.txt": "MUTUELLE ET PRÉVOYANCE : Exonération patronale limite (6% PASS + 1.5% Salaire), max 12% PASS.",
    "DOC_BOSS_APPRENTIS_EXO.txt": "APPRENTISSAGE 2026 : Exo salariale si Salaire <= 50% SMIC pour contrats post 01/03/25. Antérieurs : 79% SMIC.",
    "DOC_BOSS_JEI_RAPPEL.txt": "JEI : Exo patronale plafonnée à 4.5 SMIC par salarié et 3 PASS par établissement. Durée : 8 ans.",

    # --- 3. JURISPRUDENCE ET SÉCURITÉ JURIDIQUE (MÉMO JURISP) ---
    "DOC_JURISPRUDENCE_FORFAIT.txt": "FORFAIT JOURS : Nul si absence de suivi réel de la charge de travail. L'entretien annuel ne suffit pas à prouver le contrôle.",
    "DOC_JURISPRUDENCE_NON_CONCURRENCE.txt": "NON-CONCURRENCE : Clause nulle sans contrepartie financière. Doit être indispensable, limitée dans le temps et l'espace.",
    "DOC_JURISPRUDENCE_TELE_REVERS.txt": "TÉLÉTRAVAIL : L'employeur ne peut imposer le retour en présentiel si le télétravail est contractuel (avenant), sauf clause de réversibilité.",
    "DOC_JURISPRUDENCE_PREUVE.txt": "LOYAUTÉ DE LA PREUVE : Interdiction d'utiliser des preuves illicites (vidéosurveillance non déclarée, enregistrements clandestins).",

    # --- 4. SOCLE LÉGAL (CODE DU TRAVAIL & SS) ---
    "LEGAL_AFFILIATION_PRINCIPE.txt": "CODE SS : Solidarité nationale. Affiliation obligatoire pour tout travailleur en France. Garantie contre les risques de réduction de revenus.",
    "LEGAL_CONCERTATION_SOCIALE.txt": "CODE DU TRAVAIL : Obligation de concertation préalable avec les syndicats pour tout projet de réforme emploi/formation.",
    "LEGAL_MARINS_SPECIFICITE.txt": "MARINS : Calcul d'exonération spécifique basé sur le salaire forfaitaire d'assiette du régime spécial des marins.",
}

# Création des fichiers dans le dossier data_clean
for filename, content in knowledge_base.items():
    path = os.path.join(output_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

print(f"SUCCÈS : {len(knowledge_base)} fiches d'expertise générées dans {output_dir}/")
print("Votre base de connaissances est maintenant à jour avec les chiffres 2026.")