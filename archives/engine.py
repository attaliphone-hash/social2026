import yaml
import os
import re

class SocialRuleEngine:
    def __init__(self, rules_path="rules/social_rules.yaml"):
        self.rules = []
        if os.path.exists(rules_path):
            with open(rules_path, "r", encoding="utf-8") as f:
                self.rules = yaml.safe_load(f) or []
        
        # LISTE NOIRE : Les mots que le moteur doit ignorer absolument
        self.STOP_WORDS = {
            "le", "la", "les", "l", "d", "de", "du", "des", 
            "un", "une", "et", "ou", "à", "en", "par", "pour", 
            "dans", "sur", "avec", "sans", "sous",
            "comment", "quel", "quelle", "quels", "quelles", 
            "est", "sont", "c", "ce", "ça", "faut", "il"
        }

    def clean_query(self, query):
        """Nettoie la question pour ne garder que les mots importants"""
        # 1. Minuscules et suppression ponctuation simple
        query = query.lower()
        query = re.sub(r"[',\.!\?]", " ", query) # Remplace apostrophes et ponctuation par espace
        
        # 2. Découpage
        words = query.split()
        
        # 3. Filtrage des mots vides
        meaningful_words = [w for w in words if w not in self.STOP_WORDS and len(w) > 2]
        
        return meaningful_words

    def find_rule(self, query):
        """
        Cherche une règle correspondante de manière plus stricte.
        """
        keywords = self.clean_query(query)
        
        # Si après nettoyage il ne reste rien (ex: "C'est quoi ?"), on laisse Gemini gérer
        if not keywords:
            return None
        
        # Score de pertinence pour chaque règle
        best_rule = None
        max_score = 0
        
        for rule in self.rules:
            # On prépare le contenu de la règle (Nom + Tags + Description)
            rule_content = (rule.get('nom', '') + " " + " ".join(rule.get('tags', []))).lower()
            
            # On compte combien de mots-clés matchent
            score = 0
            for k in keywords:
                if k in rule_content:
                    score += 1
            
            # IL FAUT QU'AU MOINS UN MOT CLÉ MATCH (et on prend le meilleur score)
            if score > 0 and score > max_score:
                max_score = score
                best_rule = rule
                
        # SEUIL DE SÉCURITÉ :
        # Pour éviter les faux positifs, on peut exiger un certain niveau de confiance
        # Pour l'instant on retourne le meilleur match simple
        return best_rule

    def get_formatted_answer(self, keywords=None): # On garde la signature keywords pour compatibilité
        """
        Récupère la réponse 'parfaite' pré-rédigée pour l'IA.
        Note : keywords est ici la phrase brute (query) qu'on va nettoyer
        """
        # Si on reçoit une liste (ancien code), on la rejoint, sinon on prend la string
        query_str = " ".join(keywords) if isinstance(keywords, list) else keywords
        
        rule = self.find_rule(query_str)
            
        if rule and rule.get('type') == 'constante':
            template = rule['message_template']
            vals = rule['valeurs']
            
            formatted_msg = template
            for k, v in vals.items():
                formatted_msg = formatted_msg.replace(f"{{valeurs.{k}}}", str(v))
                
            return {
                "found": True,
                "text": formatted_msg,
                "source": rule['source_officielle'],
                "data": vals
            }
            
        return {"found": False, "text": "Aucune règle spécifique trouvée."}

# Test rapide intégré
if __name__ == "__main__":
    engine = SocialRuleEngine()
    print("--- TEST MOTEUR V4.1 ---")
    
    # Test 1 : Doit trouver (Repas)
    q1 = "Quel est le montant du repas ?"
    res1 = engine.get_formatted_answer(keywords=q1.split())
    print(f"Q: '{q1}' -> Trouvé: {res1['found']} ({res1.get('source')})")
    
    # Test 2 : Ne doit PAS trouver (Rupture -> Pas de règle YAML rupture pour l'instant)
    q2 = "Comment calculer l'indemnité de rupture ?"
    res2 = engine.get_formatted_answer(keywords=q2.split())
    print(f"Q: '{q2}' -> Trouvé: {res2['found']} (Doit être False)")