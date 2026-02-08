"""
==============================================================================
SOCIAL RULE ENGINE - MOTEUR DE RÈGLES YAML
VERSION : 4.0 (NORMALISATION AMÉLIORÉE + MATCHING ROBUSTE)
DATE : 08/02/2026
==============================================================================
"""

import yaml
import os
import re
import unicodedata
from typing import List, Dict, Optional, Set


class SocialRuleEngine:
    """
    Moteur de règles métier pour le droit social français.
    Charge les règles depuis un fichier YAML et effectue le matching
    par mots-clés avec normalisation avancée.
    """
    
    # Règles vitales toujours injectées dans le contexte
    VITAL_RULE_IDS = [
        "SMIC_2026",
        "PASS_2026",
        "MG_2026",
        "PROTOCOLE_CALCUL_SOCIAL",
        "CSG_CRDS_2026",
        "TAUX_COTISATIONS_2026"
    ]
    
    def __init__(self, yaml_path: str = "rules/social_rules.yaml"):
        """
        Initialise le moteur de règles.
        
        Args:
            yaml_path: Chemin vers le fichier YAML des règles
        """
        self.yaml_path = self._resolve_yaml_path(yaml_path)
        self.rules: List[Dict] = self._load_rules()
        self._build_keyword_index()
    
    def _resolve_yaml_path(self, yaml_path: str) -> str:
        """Résout le chemin du fichier YAML (local vs cloud)."""
        if os.path.exists(yaml_path):
            return yaml_path
        
        # Tentative avec chemin relatif
        alt_path = os.path.join("rules", "social_rules.yaml")
        if os.path.exists(alt_path):
            return alt_path
        
        # Tentative depuis le répertoire courant
        cwd_path = os.path.join(os.getcwd(), "rules", "social_rules.yaml")
        if os.path.exists(cwd_path):
            return cwd_path
        
        print(f"⚠️ Fichier YAML non trouvé: {yaml_path}")
        return yaml_path
    
    def _load_rules(self) -> List[Dict]:
        """Charge les règles depuis le fichier YAML."""
        try:
            with open(self.yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                rules = data if isinstance(data, list) else []
                print(f"✅ {len(rules)} règles chargées depuis {self.yaml_path}")
                return rules
        except FileNotFoundError:
            print(f"❌ Fichier YAML non trouvé: {self.yaml_path}")
            return []
        except yaml.YAMLError as e:
            print(f"❌ Erreur parsing YAML: {e}")
            return []
        except Exception as e:
            print(f"❌ Erreur chargement YAML: {e}")
            return []
    
    def _build_keyword_index(self) -> None:
        """Construit un index inversé des keywords pour recherche rapide."""
        self._keyword_to_rules: Dict[str, List[Dict]] = {}
        
        for rule in self.rules:
            keywords = rule.get("keywords", [])
            for kw in keywords:
                if isinstance(kw, str):
                    normalized_kw = self._normalize_text(kw)
                    if normalized_kw not in self._keyword_to_rules:
                        self._keyword_to_rules[normalized_kw] = []
                    self._keyword_to_rules[normalized_kw].append(rule)
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalise le texte pour le matching robuste.
        - Mise en minuscules
        - Suppression des accents
        - Remplacement des tirets et apostrophes par des espaces
        - Suppression des caractères spéciaux
        
        Args:
            text: Texte à normaliser
            
        Returns:
            Texte normalisé
        """
        if not text:
            return ""
        
        # Minuscules
        text = text.lower()
        
        # Suppression des accents (é -> e, ç -> c, etc.)
        text = unicodedata.normalize('NFKD', text)
        text = text.encode('ASCII', 'ignore').decode('ASCII')
        
        # Remplacement des séparateurs par des espaces
        text = text.replace("-", " ")
        text = text.replace("'", " ")
        text = text.replace("'", " ")  # Apostrophe typographique
        text = text.replace("_", " ")
        
        # Suppression des caractères spéciaux (garde lettres, chiffres, espaces)
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        
        # Normalisation des espaces multiples
        text = re.sub(r"\s+", " ", text).strip()
        
        return text
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize le texte en mots individuels normalisés.
        
        Args:
            text: Texte à tokenizer
            
        Returns:
            Liste de tokens
        """
        if not text:
            return []
        
        normalized = self._normalize_text(text)
        tokens = [w for w in normalized.split() if len(w) >= 2]  # Ignore les mots < 2 chars
        
        return tokens
    
    def match_rules(self, query: str, top_k: int = 7, min_score: int = 1) -> List[Dict]:
        """
        Match les règles YAML avec la requête utilisateur.
        
        Args:
            query: Question de l'utilisateur
            top_k: Nombre maximum de règles spécifiques à retourner
            min_score: Score minimum pour qu'une règle soit retenue
            
        Returns:
            Liste des règles matchées (vitales + spécifiques)
        """
        if not query:
            return self._get_vital_rules()
        
        query_normalized = self._normalize_text(query)
        query_tokens = self._tokenize(query)
        
        # 1. Récupération des règles vitales (toujours présentes)
        vital_rules = self._get_vital_rules()
        vital_ids = set(self.VITAL_RULE_IDS)
        
        # 2. Scoring des règles par mots-clés
        results: List[tuple] = []
        
        for rule in self.rules:
            rule_id = rule.get("id", "")
            
            # Skip les règles vitales (déjà incluses)
            if rule_id in vital_ids:
                continue
            
            rule_keywords = rule.get("keywords", [])
            if not rule_keywords:
                continue
            
            score = 0
            
            # Normalisation des keywords de la règle
            rule_kw_normalized: Set[str] = set()
            for kw in rule_keywords:
                if isinstance(kw, str):
                    rule_kw_normalized.add(self._normalize_text(kw))
            
            # Score par token exact
            for token in query_tokens:
                if token in rule_kw_normalized:
                    score += 2  # Bonus pour match exact
            
            # Score par inclusion partielle (keyword dans query)
            for kw_norm in rule_kw_normalized:
                if kw_norm in query_normalized:
                    score += 1
            
            # Bonus pour les requêtes courtes (intention forte)
            if len(query_tokens) <= 5 and score > 0:
                score += 1
            
            if score >= min_score:
                results.append((score, rule))
        
        # 3. Tri par score décroissant et sélection top_k
        results.sort(key=lambda x: x[0], reverse=True)
        matched_rules = [r for _, r in results[:top_k]]
        
        # 4. Log pour debug
        if matched_rules:
            matched_ids = [r.get("id", "?") for r in matched_rules[:3]]
            print(f"🔍 Règles matchées: {matched_ids}...")
        
        # Retourne vitales + spécifiques
        return vital_rules + matched_rules
    
    def _get_vital_rules(self) -> List[Dict]:
        """Retourne les règles vitales (SMIC, PASS, etc.)."""
        return [r for r in self.rules if r.get("id") in self.VITAL_RULE_IDS]
    
    def get_base_rules(self) -> List[Dict]:
        """
        Retourne les règles de base pour fallback.
        Alias de _get_vital_rules() pour compatibilité.
        """
        return self._get_vital_rules()
    
    def format_certified_facts(self, matched_rules: List[Dict]) -> str:
        """
        Formate les règles matchées en texte pour le prompt.
        
        Args:
            matched_rules: Liste des règles matchées
            
        Returns:
            Texte formaté des faits certifiés
        """
        if not matched_rules:
            return "(Aucune règle spécifique trouvée)"
        
        lines = []
        seen_ids: Set[str] = set()
        
        for rule in matched_rules:
            rule_id = rule.get("id", "")
            
            # Éviter les doublons
            if rule_id in seen_ids:
                continue
            seen_ids.add(rule_id)
            
            text = (rule.get("text") or "").strip()
            source = (rule.get("source") or "Règle Officielle").strip()
            
            if text:
                lines.append(f"- {text} (Source : {source})")
        
        return "\n".join(lines).strip() if lines else "(Aucune règle applicable)"
    
    def get_rule_by_id(self, rule_id: str) -> Optional[Dict]:
        """
        Récupère une règle par son ID.
        
        Args:
            rule_id: Identifiant de la règle
            
        Returns:
            Règle ou None si non trouvée
        """
        for rule in self.rules:
            if rule.get("id") == rule_id:
                return rule
        return None
    
    def get_yaml_update_date(self) -> str:
        """Récupère la date de dernière mise à jour du YAML."""
        if not self.rules:
            return "Janvier 2026"
        
        for rule in self.rules:
            if rule.get("derniere_maj"):
                return rule.get("derniere_maj")
        
        return "Janvier 2026"
    
    def get_all_keywords(self) -> List[str]:
        """Retourne la liste de tous les keywords disponibles."""
        all_kw = set()
        for rule in self.rules:
            keywords = rule.get("keywords", [])
            for kw in keywords:
                if isinstance(kw, str):
                    all_kw.add(kw.lower())
        return sorted(list(all_kw))
    
    def search_rules_by_keyword(self, keyword: str) -> List[Dict]:
        """
        Recherche toutes les règles contenant un keyword spécifique.
        
        Args:
            keyword: Mot-clé à rechercher
            
        Returns:
            Liste des règles contenant ce keyword
        """
        keyword_normalized = self._normalize_text(keyword)
        return self._keyword_to_rules.get(keyword_normalized, [])
    
    def get_stats(self) -> Dict:
        """Retourne des statistiques sur les règles chargées."""
        total_rules = len(self.rules)
        rules_with_keywords = sum(1 for r in self.rules if r.get("keywords"))
        total_keywords = sum(len(r.get("keywords", [])) for r in self.rules)
        
        return {
            "total_rules": total_rules,
            "rules_with_keywords": rules_with_keywords,
            "rules_without_keywords": total_rules - rules_with_keywords,
            "total_keywords": total_keywords,
            "avg_keywords_per_rule": round(total_keywords / max(total_rules, 1), 1),
            "yaml_path": self.yaml_path,
            "last_update": self.get_yaml_update_date()
        }
    
    def validate_yaml(self) -> Dict:
        """
        Valide le fichier YAML et retourne un rapport.
        
        Returns:
            Dictionnaire avec le rapport de validation
        """
        issues = []
        warnings = []
        
        seen_ids = set()
        
        for i, rule in enumerate(self.rules):
            rule_id = rule.get("id", f"RULE_{i}")
            
            # Vérification ID unique
            if rule_id in seen_ids:
                issues.append(f"ID dupliqué: {rule_id}")
            seen_ids.add(rule_id)
            
            # Vérification keywords présents
            if not rule.get("keywords"):
                warnings.append(f"Pas de keywords: {rule_id}")
            
            # Vérification texte présent
            if not rule.get("text"):
                warnings.append(f"Pas de texte: {rule_id}")
            
            # Vérification source présente
            if not rule.get("source"):
                warnings.append(f"Pas de source: {rule_id}")
            
            # Vérification valeurs numériques
            valeurs = rule.get("valeurs", {})
            if valeurs:
                for key, val in valeurs.items():
                    if isinstance(val, (int, float)) and val < 0:
                        warnings.append(f"Valeur négative {key} dans {rule_id}")
        
        return {
            "valid": len(issues) == 0,
            "total_rules": len(self.rules),
            "issues": issues,
            "warnings": warnings,
            "issues_count": len(issues),
            "warnings_count": len(warnings)
        }


# ==============================================================================
# TESTS UNITAIRES (exécutés si lancé directement)
# ==============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("TEST DU MOTEUR DE RÈGLES SOCIAL V4.0")
    print("=" * 60)
    
    # Initialisation
    engine = SocialRuleEngine()
    
    # Stats
    stats = engine.get_stats()
    print(f"\n📊 STATISTIQUES:")
    for key, val in stats.items():
        print(f"   {key}: {val}")
    
    # Validation
    validation = engine.validate_yaml()
    print(f"\n✅ VALIDATION:")
    print(f"   Valide: {validation['valid']}")
    print(f"   Issues: {validation['issues_count']}")
    print(f"   Warnings: {validation['warnings_count']}")
    
    if validation['warnings'][:5]:
        print(f"   Premiers warnings: {validation['warnings'][:5]}")
    
    # Tests de matching
    test_queries = [
        "indemnité télétravail 3 jours par semaine",
        "forfait social rupture conventionnelle",
        "calcul indemnité licenciement",
        "ticket restaurant plafond exonération",
        "smic 2026",
        "période essai cadre",
        "ijss maladie",
        "prime partage valeur ppv"
    ]
    
    print(f"\n🔍 TESTS DE MATCHING:")
    for query in test_queries:
        matched = engine.match_rules(query, top_k=3)
        specific = [r.get("id") for r in matched if r.get("id") not in engine.VITAL_RULE_IDS]
        print(f"   '{query[:40]}...' -> {specific[:3]}")
    
    # Test normalisation
    print(f"\n🔤 TESTS NORMALISATION:")
    test_texts = [
        "Télétravail",
        "télé-travail",
        "TELETRAVAIL",
        "préavis",
        "preavis",
        "congés payés",
        "conges payes"
    ]
    
    for text in test_texts:
        normalized = engine._normalize_text(text)
        print(f"   '{text}' -> '{normalized}'")
    
    print("\n" + "=" * 60)
    print("TESTS TERMINÉS")
    print("=" * 60)
