from pathlib import Path
from typing import Optional, Dict, Any
from xml.dom import minidom
from src.config import CLIENT_ID, CLIENT_KEY, REALM, PROXIES
from src.utils import FileHandler, XMLValidator
from .auth import TokenManager
from .templates import XMLTemplates
import json
import requests
import time

class RuleBridge:
    def __init__(self, json_file: str = "examples/rules/rule.json",
                 max_wait_time: int = 300,  # 5 minutes default timeout
                 check_interval: int = 5):   # 5 seconds between checks
        self.json_file = json_file
        self.token_manager = TokenManager()
        self.file_handler = FileHandler()
        self.xml_validator = XMLValidator()
        self.templates = XMLTemplates()
        
        # Polling configuration
        self.max_wait_time = max_wait_time
        self.check_interval = check_interval
        
        # Initialize token manager
        self.token_manager.ensure_valid_token()

    def map_pmd_severity_to_sonar(self, pmd_severity):
        """
        Maps PMD severity to Sonarqube format
        PMD: 1 (blocker) -> 5 (info)
        Sonar: BLOCKER, CRITICAL, MAJOR, MINOR, INFO
        """
        severity_map = {
            "1": "BLOCKER",
            "2": "CRITICAL",
            "3": "MAJOR",
            "4": "MINOR",
            "5": "INFO"
        }
        return severity_map.get(str(pmd_severity), "INFO")

    def create_sonar_rule(self, pmd_rule):
        """
        Converts a PMD rule to Sonarqube 9.9 LTS format
        """
        return {
            "key": pmd_rule.get("name", "unknown_rule"),
            "name": pmd_rule.get("name", "Unknown Rule"),
            "status": "ready",
            "type": "CODE_SMELL",
            "severity": self.map_pmd_severity_to_sonar(pmd_rule.get("priority", "5")),
            "description": pmd_rule.get("message", "No description available"),
            "tags": ["pmd"],
            "remediation": {
                "func": "Constant/Issue",
                "constantCost": "5min"
            },
            "debtRemediationFunctionCoefficient": "5min",
            "scope": "MAIN"
        }

    def save_sonar_rules(self, rules, output_file="rules.json"):
        """
        Saves rules in Sonarqube 9.9 LTS format
        """
        try:
            sonar_rules = {
                "rules": [self.create_sonar_rule(rule) for rule in rules],
                "metadata": {
                    "formatVersion": "9.9",
                    "repository": "pmd-to-sonar",
                    "name": "PMD Rules converted to Sonarqube",
                    "language": "java"
                }
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(sonar_rules, f, indent=2, ensure_ascii=False)
                
            print(f"Rules file successfully saved to: {output_file}")
            
        except Exception as e:
            print(f"Error saving rules file: {str(e)}")
            return None

    def convert_pmd_to_sonar(self, pmd_report):
        """
        Converts PMD report in SARIF format to Sonarqube JSON
        """
        sonar_issues = []
        
        try:
            for violation in pmd_report.get('violations', []):
                issue = {
                    "engineId": "pmd",
                    "ruleId": violation.get('rule', 'unknown'),
                    "severity": self.map_pmd_severity_to_sonar(violation.get('priority')),
                    "type": "CODE_SMELL",
                    "primaryLocation": {
                        "message": violation.get('description', ''),
                        "filePath": violation.get('file', ''),
                        "textRange": {
                            "startLine": violation.get('beginline', 1),
                            "endLine": violation.get('endline', 1),
                            "startColumn": violation.get('begincolumn', 1),
                            "endColumn": violation.get('endcolumn', 1)
                        }
                    }
                }
                sonar_issues.append(issue)
            
            return {
                "issues": sonar_issues,
                "total": len(sonar_issues)
            }
            
        except Exception as e:
            print(f"Error converting report: {str(e)}")
            return None

    def wait_for_ai_response(self, response_id: str, headers: Dict) -> Optional[Dict]:
        """
        Wait for AI response with timeout
        
        Args:
            response_id: ID of the AI request to check
            headers: Authentication headers
            
        Returns:
            Response data if successful, None if timeout or error
        """
        start_time = time.time()
        
        while (time.time() - start_time) < self.max_wait_time:
            try:
                response = requests.get(
                    f"{self.token_manager.get_url}/{response_id}",
                    headers=headers,
                    proxies=PROXIES
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'completed':
                        return data
                    elif data.get('status') == 'failed':
                        print(f"AI processing failed: {data.get('error', 'Unknown error')}")
                        return None
                elif response.status_code != 202:  # 202 means still processing
                    print(f"Error checking AI status: {response.status_code}")
                    return None
                
            except Exception as e:
                print(f"Error during AI response check: {e}")
                return None
            
            time.sleep(self.check_interval)
        
        print(f"Timeout waiting for AI response after {self.max_wait_time} seconds")
        return None

    def process_natural_language_rule(self):
        """
        Process natural language rule and convert to PMD XML
        using Stackspot AI only for XPath generation
        """
        try:
            # Get valid token headers
            headers = self.token_manager.ensure_valid_token()
            
            # Read JSON configuration
            rule_config = self.file_handler.read_json(Path(self.json_file))
            if not rule_config:
                return None

            # Build XPath prompt for AI
            xpath_prompt = f"""
            Create a PMD XPath expression that implements the following rule:
            
            Description: {rule_config['rule']['what_to_find']}
            
            The expression must be valid for PMD and detect the problem shown in the bad example:
            
            Problem code:
            {rule_config['rule']['examples']['bad']}
            
            Correct code:
            {rule_config['rule']['examples']['good']}
            
            Return ONLY the XPath expression, without explanations.
            """
            
            xpath_payload = {
                'prompt': xpath_prompt,
                'temperature': 0.3,
                'max_tokens': 500
            }
            
            # Initial request to AI
            initial_response = requests.post(
                self.token_manager.post_url,
                headers=headers,
                json=xpath_payload,
                proxies=PROXIES
            )
            
            if initial_response.status_code != 202:  # 202 means accepted for processing
                print(f"Error submitting to AI: {initial_response.status_code}")
                return None
            
            # Get request ID and wait for completion
            request_id = initial_response.json().get('request_id')
            if not request_id:
                print("No request ID received from AI")
                return None
            
            # Wait for AI processing
            ai_response = self.wait_for_ai_response(request_id, headers)
            if not ai_response:
                return None
            
            xpath_expression = ai_response['result']['choices'][0]['text'].strip()
            
            # Build XML using templates
            rule_xml = self.templates.RULE_TEMPLATE.format(
                name=rule_config['rule']['name'],
                language=rule_config['rule']['language'],
                message=rule_config['rule']['description'],
                description=rule_config['rule']['description'],
                severity=rule_config['rule']['severity'],
                xpath=xpath_expression,
                good_example=rule_config['rule']['examples']['good'],
                bad_example=rule_config['rule']['examples']['bad']
            )
            
            complete_xml = f"{self.templates.XML_HEADER}{rule_xml}{self.templates.XML_FOOTER}"
            
            # Parse and format XML
            xml_dom = minidom.parseString(complete_xml)
            pretty_xml = xml_dom.toprettyxml(indent="  ")
            
            # Save formatted XML rule
            xml_file = Path(self.json_file).with_suffix('.xml')
            if self.file_handler.write_xml(pretty_xml, xml_file):
                # Validate generated XML
                if self.xml_validator.validate_pmd_rule(xml_file):
                    print(f"XML rule successfully generated: {xml_file}")
                    return xml_file
                else:
                    print("Generated XML is not valid for PMD")
                    return None
                    
        except Exception as e:
            print(f"Error processing rule: {e}")
            return None

    def process(self) -> None:
        """
        Execute the complete flow to generate XML rule
        """
        try:
            # Generate XML rule from natural language
            xml_rule = self.process_natural_language_rule()
            if not xml_rule:
                return

            print(f"XML rule generated successfully. Now run:")
            print(f"./analyze.sh {xml_rule} <source_code_path>")

        except Exception as e:
            print(f"Error during execution: {e}") 