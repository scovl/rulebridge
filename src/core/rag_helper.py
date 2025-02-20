from pathlib import Path
from typing import Dict, Optional, List
import json

class PMDRuleHelper:
    def __init__(self):
        self.rules_db = {
            'java': self._load_rules('java'),
            'xml': self._load_rules('xml'),
            # add other languages as needed
        }

    def _load_rules(self, language: str) -> Dict:
        """
        Load rule patterns and capabilities for a specific language
        """
        try:
            rules_file = Path(f'src/core/rules/{language}_rules.json')
            with open(rules_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading rules for {language}: {e}")
            return {}

    def validate_rule_feasibility(self, language: str, description: str) -> Dict:
        """
        Check if PMD can handle the requested rule
        """
        if language not in self.rules_db:
            return {
                'feasible': False,
                'message': f"PMD does not support rules for {language}"
            }

        # Analyze description against known patterns
        capabilities = self.rules_db[language]
        matches = self._match_capabilities(description, capabilities)

        if not matches:
            return {
                'feasible': False,
                'message': f"""
                PMD might not be able to implement this rule for {language}.
                
                PMD {language} rules typically handle:
                {self._format_capabilities(capabilities['supported_patterns'])}
                
                Consider checking PMD documentation or using a different tool.
                """
            }

        return {
            'feasible': True,
            'matched_patterns': matches
        }

    def _match_capabilities(self, description: str, capabilities: Dict) -> List[str]:
        """Match rule description against known capabilities"""
        matches = []
        for pattern in capabilities['supported_patterns']:
            if any(keyword in description.lower() for keyword in pattern['keywords']):
                matches.append(pattern['name'])
        return matches 