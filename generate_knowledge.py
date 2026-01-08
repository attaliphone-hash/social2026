import os

# Configuration du dossier de sortie
output_dir = "data_clean"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Base de connaissances complète extraite de nos analyses BOSS
knowledge_base = {
    # --- PLAFONDS ET CHIFFRES CLÉS ---
    "REF_2025_BAREMES_PLAFOND.txt": "Plafond Sécurité Sociale 2025 : Annuel 47100€, Mensuel 3925€, Horaire 29€.",
    "REF_2025_BAREMES_AVN_REPAS.txt": "Avantages Nature Repas 2025 : Forfait 5.40€/repas, 10.80€/jour. HCR (MG) : 4.15€.",
    "REF_2025_BAREMES_FRAIS_REPAS.txt": "Frais Pro Repas 2025 : Resto (déplacement) 21.00€, Hors resto 10.10€, Lieu travail 7.50€.",
    "REF_2025_BAREMES_STAGIAIRES.txt": "Gratification Stagiaire 2025 : Franchise de cotisations à 4.35€/heure (15% du plafond horaire).",
    "REF_2025_BAREMES_HS_TAUX.txt": "Heures Supp 2025 : Taux réduction salariale max 11.31%. Déduction patronale : 1.50€ (<20 sal) ou 0.50€ (20-249 sal).",
    "REF_2025_BAREMES_PPV.txt": "Prime Partage Valeur 2025 : Plafond 3000€ ou 6000€ (si accord intéressement).",

    # --- DOCTRINE ET RÈGLES DE CALCUL ---
    "DOC_BOSS_ALLEGEMENTS_FILLON.txt": "Réduction Générale 2025 : Valeur T max 31.94% (FNAL 0.1%) ou 32.34% (FNAL 0.5%). Evolution au 1er mai 2025.",
    "DOC_BOSS_ASSIETTE_CSG.txt": "Assiette CSG/CRDS : 98.25% du brut (abattement 1.75% plafonné à 4 PASS).",
    "DOC_BOSS_AVN_VEHICULE_ELEC.txt": "Véhicules Electriques 2025 : Abattement de 70% sur l'avantage, plafonné à 4582€/an.",
    "DOC_BOSS_FRAIS_TELETRAVAIL.txt": "Télétravail 2025 : Exonération 2.70€/jour (max 59.40€/mois) ou 10.90€/mois pour 1j/semaine.",
    "DOC_BOSS_EFFECTIF_CALCUL.txt": "Effectif Moyen Annuel (EMA) : Moyenne des effectifs au dernier jour de chaque mois de l'année N-1.",
    "DOC_BOSS_RUPTURE_CONV.txt": "Rupture Conventionnelle (Post 01/09/23) : Contribution patronale unique de 30% sur la part exonérée.",
    "DOC_BOSS_MNS_CALCUL.txt": "Montant Net Social : Sommes brutes moins cotisations sociales salariales obligatoires.",
    "DOC_BOSS_PSC_SANTE.txt": "Protection Sociale Complémentaire : Exonération patronale limite (6% PASS + 1.5% Salaire), max 12% PASS.",
    "DOC_BOSS_APPRENTIS_EXO.txt": "Apprentis 2025 : Exo salariale si Salaire <= 79% SMIC. Exo CSG/CRDS si Salaire <= 50% SMIC.",
    "DOC_BOSS_JEI_RAPPEL.txt": "JEI 2025 : Exo patronale plafonnée à 4.5 SMIC par salarié et 3 PASS par établissement.",
    "DOC_BOSS_ZONEES_ZFRR.txt": "Zones ZFRR (ex-ZRR) : Exo patronale dégressive entre 1.5 et 2.4 SMIC.",

    # --- FORMALITÉS ---
    "DOC_BOSS_PAIE_MENTIONS.txt": "Bulletin de paie : Mentions obligatoires (Siret, NAF, Net Social). Interdiction de mentionner grève ou délégués.",
}

# Création des fichiers
for filename, content in knowledge_base.items():
    path = os.path.join(output_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

print(f"TERMINÉ : {len(knowledge_base)} fiches d'expertise générées dans {output_dir}/")