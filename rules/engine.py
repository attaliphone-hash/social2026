import yaml
import os
import re

class SocialRuleEngine:
    def __init__(self, yaml_path="rules/social_rules.yaml"):
        # On remonte d'un niveau si besoin pour trouver le fichier
        if not os.path.exists(yaml_path):
            if os.path.exists(os.path.join("rules", "social_rules.yaml")):
                self.yaml_path = os.path.join("rules", "social_rules.yaml")
            else:
                self.yaml_path = yaml_path
        else:
            self.yaml_path = yaml_path

        self.rules = self._load_rules()

    def _load_rules(self):
        """Charge les règles depuis le fichier YAML"""
        try:
            with open(self.yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data if isinstance(data, list) else []
        except Exception as e:
            print(f"Erreur chargement YAML: {e}")
            return []

    def _tokenize(self, text: str):
        """Tokenisation simple, robuste au français (accents inclus)"""
        if not text:
            return []
        text = text.lower()
        # on garde lettres/chiffres/accents, on remplace le reste par espace
        text = re.sub(r"[^0-9a-zàâäçéèêëîïôöùûüÿñæœ'\s-]", " ", text)
        text = text.replace("-", " ")
        words = [w.strip("'") for w in text.split() if w.strip("'")]
        return words

    def match_rules(self, query: str, top_k: int = 5, min_score: int = 2):
        """
        Renvoie les meilleures règles correspondant à la requête.
        - min_score=2 évite les déclenchements “au hasard” (1 seul mot).
        """
        if not query:
            return []

        query_words = self._tokenize(query)
        if not query_words:
            return []

        results = []

        for rule in self.rules:
            rule_keywords = [k.lower() for k in rule.get("keywords", []) if isinstance(k, str)]
            if not rule_keywords:
                continue

            # Score = nombre de mots présents + bonus si un mot-clé exact est présent
            score = 0
            rule_kw_set = set(rule_keywords)

            for w in query_words:
                if w in rule_kw_set:
                    score += 1

            # Bonus si la requête contient exactement un mot-clé fort (ex: "smic")
            # (utile pour les requêtes courtes)
            if len(query_words) <= 3:
                for kw in rule_keywords:
                    if kw in query.lower():
                        score += 2

            if score >= min_score:
                results.append((score, rule))

        results.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in results[:top_k]]

    def format_certified_facts(self, matched_rules):
        """
        Formate une section “faits certifiés” à injecter dans le prompt.
        """
        if not matched_rules:
            return ""

        lines = []
        for r in matched_rules:
            text = (r.get("text") or "").strip()
            src = (r.get("source") or "Règle Officielle").strip()
            if text:
                # Format volontairement compact, lisible, et “copiable” par le modèle
                lines.append(f"- {text} (Source : {src})")

        return "\n".join(lines).strip()
