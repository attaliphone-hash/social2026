import yaml
import os
import re

class SocialRuleEngine:
    def __init__(self, yaml_path="rules/social_rules.yaml"):
        # Gestion robuste du chemin (local vs cloud)
        if not os.path.exists(yaml_path):
            if os.path.exists(os.path.join("rules", "social_rules.yaml")):
                self.yaml_path = os.path.join("rules", "social_rules.yaml")
            else:
                self.yaml_path = yaml_path
        else:
            self.yaml_path = yaml_path

        self.rules = self._load_rules()

    def _load_rules(self):
        try:
            with open(self.yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data if isinstance(data, list) else []
        except Exception as e:
            print(f"Erreur chargement YAML: {e}")
            return []

    def _tokenize(self, text: str):
        if not text:
            return []
        text = text.lower()
        # Nettoyage standard pour le matching
        text = re.sub(r"[^0-9a-zàâäçéèêëîïôöùûüÿñæœ'\s-]", " ", text)
        text = text.replace("-", " ")
        words = [w.strip("'") for w in text.split() if w.strip("'")]
        return words

    def match_rules(self, query: str, top_k: int = 7, min_score: int = 1):
        # MODIF 1 : top_k passé à 7 pour avoir plus de contexte
        # MODIF 2 : min_score passé à 1 (CRITIQUE pour ne rien rater)
        
        if not query:
            return []

        query_words = self._tokenize(query)
        
        # 1. LE SOCLE : Récupération systématique des constantes vitales
        # Ajout de CSG_CRDS pour garantir les calculs Brut > Net
        vital_ids = [
            "SMIC_2026", 
            "PASS_2026", 
            "MG_2026", 
            "PROTOCOLE_CALCUL_SOCIAL",
            "CSG_CRDS_2026" 
        ]
        vital_rules = [r for r in self.rules if r.get("id") in vital_ids]

        # 2. RECHERCHE PAR MOTS-CLÉS
        results = []
        for rule in self.rules:
            if rule.get("id") in vital_ids:
                continue

            rule_keywords = [k.lower() for k in rule.get("keywords", []) if isinstance(k, str)]
            if not rule_keywords:
                continue

            score = 0
            rule_kw_set = set(rule_keywords)
            
            # Score par mot exact
            for w in query_words:
                if w in rule_kw_set:
                    score += 1

            # Bonus pour les requêtes courtes (détection d'intention forte)
            if len(query_words) <= 4: # J'ai élargi un peu la notion de "courte"
                for kw in rule_keywords:
                    if kw in query.lower(): # Matching partiel accepté pour les mots courts
                        score += 1

            if score >= min_score:
                results.append((score, rule))

        results.sort(key=lambda x: x[0], reverse=True)
        matched_rules = [r for _, r in results[:top_k]]

        # Retourne les règles vitales + les règles spécifiques trouvées
        return vital_rules + matched_rules

    def format_certified_facts(self, matched_rules):
        if not matched_rules:
            return ""

        lines = []
        # On utilise un set pour éviter les doublons si une règle vitale est aussi matchée par mot-clé
        seen_ids = set()
        
        for r in matched_rules:
            r_id = r.get("id")
            if r_id in seen_ids:
                continue
            seen_ids.add(r_id)
            
            text = (r.get("text") or "").strip()
            src = (r.get("source") or "Règle Officielle").strip()
            if text:
                lines.append(f"- {text} (Source : {src})")

        return "\n".join(lines).strip()

    def get_yaml_update_date(self):
        """Récupère la date de dernière mise à jour définie dans le YAML."""
        if not self.rules:
            return "Janvier 2026"
        for r in self.rules:
            if r.get("derniere_maj"):
                return r.get("derniere_maj")
        return "Janvier 2026"

    def get_rule_value(self, rule_id: str, value_key: str):
        """
        Extrait une valeur numérique précise du YAML.
        """
        for rule in self.rules:
            if rule.get("id") == rule_id:
                valeurs = rule.get("valeurs", {})
                return valeurs.get(value_key)
        return None