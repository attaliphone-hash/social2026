import yaml
import os

class SocialRuleEngine:
    def __init__(self, yaml_path="rules/social_rules.yaml"):
        # On remonte d'un niveau si besoin pour trouver le fichier
        if not os.path.exists(yaml_path):
            # Si on est exécuté depuis la racine, le chemin est direct
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
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Erreur chargement YAML: {e}")
            return []

    def get_formatted_answer(self, keywords):
        """Cherche une réponse basée sur les mots-clés"""
        if not keywords:
            return {"found": False}

        query_words = keywords.lower().split()
        best_match = None
        max_score = 0

        for rule in self.rules:
            # On compte combien de mots-clés de la règle sont présents dans la question
            score = 0
            rule_keywords = [k.lower() for k in rule.get("keywords", [])]
            
            for word in query_words:
                if word in rule_keywords:
                    score += 1
            
            # Si on trouve le mot exact (ex: "smic"), gros bonus
            if keywords.lower() in rule_keywords:
                score += 10

            if score > max_score and score > 0:
                max_score = score
                best_match = rule

        if best_match and max_score >= 1:
            # On formate la réponse trouvée
            # Si c'est un tableau de valeurs (SMIC, etc.)
            valeurs = best_match.get("valeurs", {})
            text = best_match.get("text", "")
            
            # Si on a des valeurs, on peut les formater joliment si besoin, 
            # mais ici on renvoie le texte pré-rédigé du YAML qui est plus parlant.
            return {
                "found": True,
                "text": text,
                "source": f"[{best_match.get('source', 'Règle Officielle')}]"
            }

        return {"found": False}