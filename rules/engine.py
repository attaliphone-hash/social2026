import yaml
import os
import re

class SocialRuleEngine:
    def __init__(self, yaml_path="rules/social_rules.yaml"):
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
        text = re.sub(r"[^0-9a-zàâäçéèêëîïôöùûüÿñæœ'\s-]", " ", text)
        text = text.replace("-", " ")
        words = [w.strip("'") for w in text.split() if w.strip("'")]
        return words

    def match_rules(self, query: str, top_k: int = 5, min_score: int = 2):
        if not query:
            return []

        query_words = self._tokenize(query)
        
        # 1. RÉCUPÉRATION SYSTÉMATIQUE DES CONSTANTES (Le "Socle")
        # Ces IDs doivent correspondre exactement à ceux de ton YAML
        vital_ids = ["SMIC_2026", "PASS_2026", "MG_2026"]
        vital_rules = [r for r in self.rules if r.get("id") in vital_ids]

        # 2. RECHERCHE PAR MOTS-CLÉS (La "Règle métier")
        results = []
        for rule in self.rules:
            # On ne recalcule pas le score pour les constantes déjà isolées
            if rule.get("id") in vital_ids:
                continue

            rule_keywords = [k.lower() for k in rule.get("keywords", []) if isinstance(k, str)]
            if not rule_keywords:
                continue

            score = 0
            rule_kw_set = set(rule_keywords)
            for w in query_words:
                if w in rule_kw_set:
                    score += 1

            if len(query_words) <= 3:
                for kw in rule_keywords:
                    if kw in query.lower():
                        score += 2

            if score >= min_score:
                results.append((score, rule))

        results.sort(key=lambda x: x[0], reverse=True)
        matched_rules = [r for _, r in results[:top_k]]

        # 3. FUSION (Constantes + Règles spécifiques)
        # On place les constantes en premier pour qu'elles soient lues en priorité
        return vital_rules + matched_rules

    def format_certified_facts(self, matched_rules):
        if not matched_rules:
            return ""

        lines = []
        for r in matched_rules:
            text = (r.get("text") or "").strip()
            src = (r.get("source") or "Règle Officielle").strip()
            if text:
                lines.append(f"- {text} (Source : {src})")

        return "\n".join(lines).strip()