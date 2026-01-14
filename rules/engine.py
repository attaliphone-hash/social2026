import yaml
import os
import re
import unicodedata

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

    def _normalize(self, s: str) -> str:
        """Normalise une chaîne : minuscules, suppression accents, ponctuation simplifiée."""
        if not s:
            return ""
        s = s.lower().strip()
        s = unicodedata.normalize("NFD", s)
        s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")  # retire accents
        s = re.sub(r"[-_/]", " ", s)  # tirets/underscores -> espace
        s = re.sub(r"[^\w\s]", " ", s)  # ponctuation -> espace
        s = re.sub(r"\s+", " ", s).strip()
        return s

    def get_formatted_answer(self, keywords: str):
        """Cherche une réponse basée sur les mots-clés / expressions."""
        if not keywords:
            return {"found": False}

        query_norm = self._normalize(keywords)
        if not query_norm:
            return {"found": False}

        query_words = query_norm.split()

        best_match = None
        max_score = 0

        for rule in self.rules:
            score = 0
            rule_keywords_raw = rule.get("keywords", []) or []
            rule_keywords = [self._normalize(k) for k in rule_keywords_raw if isinstance(k, str) and k.strip()]

            # 1) Bonus si une expression complète est trouvée dans la question
            for rk in rule_keywords:
                if rk and len(rk.split()) >= 2 and rk in query_norm:
                    score += 12

            # 2) Matching mot à mot sur keywords simples
            for w in query_words:
                if w in rule_keywords:
                    score += 3

            # 3) Bonus léger si un mot de la question est contenu dans une expression keyword
            # (utile pour "securite sociale", "plafond mensuel", etc.)
            for rk in rule_keywords:
                if len(rk.split()) >= 2:
                    for w in query_words:
                        if w and w in rk.split():
                            score += 1

            # 4) Gros bonus si la requête normalisée correspond exactement à un keyword
            if query_norm in rule_keywords:
                score += 15

            if score > max_score:
                max_score = score
                best_match = rule

        if best_match and max_score >= 3:
            text = best_match.get("text", "")
            return {
                "found": True,
                "text": text,
                "source": f"[{best_match.get('source', 'Règle Officielle')}]"
            }

        return {"found": False}
