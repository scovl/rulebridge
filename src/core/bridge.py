from pathlib import Path
from typing import Optional, Dict, Any
from xml.dom import minidom
from src.config import CLIENT_ID, CLIENT_KEY, REALM, PROXIES
from src.utils import FileHandler, XMLValidator
from .auth import TokenManager
from .templates import XMLTemplates
from .constants import PMD_RULE_METADATA, SEVERITY_MAPPING, PMD_SONAR_MAPPING
from .ast_manager import ASTManager
from .analyzer import PMDAnalyzer
from .rag_helper import PMDRuleHelper
import json
import requests
import time

class RuleBridge:
    def __init__(self, json_file: str = "examples/rules/rule.json"):
        self.json_file = json_file
        self.token_manager = TokenManager()
        self.file_handler = FileHandler()
        self.xml_validator = XMLValidator()
        self.templates = XMLTemplates()
        self.ast_manager = ASTManager()
        self.analyzer = PMDAnalyzer()

    def process(self) -> None:
        """
        Execute the complete flow to generate XML rule
        """
        try:
            # Get valid token headers
            headers = self.token_manager.ensure_valid_token()
            
            # Read JSON configuration
            rule_config = self.file_handler.read_json(Path(self.json_file))
            if not rule_config:
                return None

            # Validate rule feasibility
            helper = PMDRuleHelper()
            feasibility = helper.validate_rule_feasibility(
                rule_config['rule']['language'],
                rule_config['rule']['what_to_find']
            )

            if not feasibility['feasible']:
                print(feasibility['message'])
                return None

            # Get AST from bad example
            ast_data = self.ast_manager.analyze_examples(rule_config['rule'])
            if not ast_data['ast']:
                return None

            # Generate XPath via AI
            xpath_expression = self._get_xpath_from_ai(headers, rule_config, ast_data)
            if not xpath_expression:
                return None

            # Generate and validate XML rule
            xml_file = self._generate_xml_rule(rule_config, xpath_expression)
            if not xml_file:
                return None

            print(f"XML rule generated successfully: {xml_file}")

        except Exception as e:
            print(f"Error during execution: {e}")

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

    def extract_sonar_metadata(self, description: str) -> Dict:
        """
        Extract Sonarqube metadata from PMD rule description tag
        
        Args:
            description: PMD rule description containing type and effort tags
            
        Returns:
            Dictionary with Sonarqube metadata
        """
        type_tag = None
        effort_tag = None
        
        # Extract tags from description [TYPE][EFFORT]
        for tag in PMD_SONAR_MAPPING['DESCRIPTION_TAG'].keys():
            if tag in description:
                type_tag = tag
                break
        
        for tag in PMD_SONAR_MAPPING['EFFORT'].keys():
            if tag in description:
                effort_tag = tag
                break
        
        return {
            'type': PMD_SONAR_MAPPING['DESCRIPTION_TAG'].get(type_tag, {'type': 'CODE_SMELL'})['type'],
            'debt': PMD_SONAR_MAPPING['EFFORT'].get(effort_tag, '20min')
        }

    def create_sonar_rule(self, pmd_rule):
        """
        Converts a PMD rule to Sonarqube format with proper metadata mapping
        """
        # Extract type and debt from description tag
        metadata = self.extract_sonar_metadata(pmd_rule.get('description', ''))
        
        return {
            "key": pmd_rule.get("name", "unknown_rule"),
            "name": pmd_rule.get("name", "Unknown Rule"),
            "status": "ready",
            "type": metadata['type'],
            "severity": PMD_SONAR_MAPPING['SEVERITY'].get(
                int(pmd_rule.get("priority", "3")), "MAJOR"
            ),
            "description": pmd_rule.get("message", "No description available"),
            "tags": ["pmd"],
            "remediation": {
                "func": "Constant/Issue",
                "constantCost": metadata['debt']
            },
            "debtRemediationFunctionCoefficient": metadata['debt'],
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
        
        while (time.time() - start_time) < 300:  # 5 minutes default timeout
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
            
            time.sleep(5)  # 5 seconds between checks
        
        print(f"Timeout waiting for AI response after 300 seconds")
        return None

    def read_ast_file(self, file_path: str = "code_ast.json") -> Optional[Dict]:
        """
        Read and parse the AST file generated by PMD
        """
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading AST file: {e}")
            return None

    def get_ai_payload(self, prompt: str, engine: str = "stackspot") -> Dict:
        """
        Build AI payload based on engine type
        
        Args:
            prompt: The prompt text to send
            engine: AI engine name (stackspot, gpt, deepseek, etc)
            
        Returns:
            Dictionary with engine-specific payload
        """
        # Base payload used by all engines
        payload = {
            'prompt': prompt
        }
        
        # Add engine-specific parameters
        if engine == "gpt":
            payload.update({
                'temperature': 0.3,
                'max_tokens': 500
            })
        elif engine == "deepseek":
            payload.update({
                'temperature': 0.3,
                'max_tokens': 500,
                'top_p': 0.95
            })
        # stackspot uses only prompt
        # add more engines as needed
        
        return payload

    def _get_xpath_from_ai(self, headers: Dict, rule_config: Dict, ast_data: Dict) -> Optional[str]:
        """
        Get XPath expression from AI
        
        Args:
            headers: Authentication headers
            rule_config: Rule configuration
            ast_data: AST data
            
        Returns:
            XPath expression if successful, None if error
        """
        try:
            # Get AST from bad example
            ast_data = self.ast_manager.analyze_examples(rule_config['rule'])
            if not ast_data['ast']:
                return None

            # Build enhanced XPath prompt with example AST
            xpath_prompt = f"""
            Create a PMD XPath expression that implements the following rule:
            
            Description: {rule_config['rule']['what_to_find']}
            
            The expression must be valid for PMD and detect the problem shown in the bad example.
            
            Problem code (what to find):
            {rule_config['rule']['examples']['bad']}
            
            AST of problem code:
            {json.dumps(ast_data['ast'], indent=2)}
            
            Reference code (correct implementation):
            {rule_config['rule']['examples']['good']}
            
            Using the AST structure of the problem code and comparing with the reference code,
            create an XPath expression that will match this problematic pattern.
            Return ONLY the XPath expression, without explanations.
            """
            
            # Get engine-specific payload
            xpath_payload = self.get_ai_payload(xpath_prompt, engine="stackspot")
            
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
            
            return xpath_expression
            
        except Exception as e:
            print(f"Error getting XPath from AI: {e}")
            return None

    def _generate_xml_rule(self, rule_config: Dict, xpath_expression: str) -> Optional[Path]:
        """
        Generate and validate XML rule
        
        Args:
            rule_config: Rule configuration
            xpath_expression: XPath expression
            
        Returns:
            XML file path if successful, None if error
        """
        try:
            # Build XML using templates and constants
            rule_xml = self.templates.RULE_TEMPLATE.format(
                name=rule_config['rule']['name'],
                language=rule_config['rule']['language'],
                message=rule_config['rule']['description'],
                rule_class=PMD_RULE_METADATA['RULE_CLASS'],
                severity_tag=SEVERITY_MAPPING[rule_config['rule']['severity']],
                severity=rule_config['rule']['severity'],
                xpath=xpath_expression
            )
            
            complete_xml = f"{self.templates.XML_HEADER}{rule_xml}{self.templates.XML_FOOTER}"
            
            # Parse and format XML
            xml_dom = minidom.parseString(complete_xml)
            pretty_xml = xml_dom.toprettyxml(indent="  ")
            
            # Save formatted XML rule
            xml_file = Path(self.json_file).with_suffix('.xml')
            if self.file_handler.write_xml(pretty_xml, xml_file):
                # Validate generated XML by testing it
                if self.xml_validator.validate_pmd_rule(xml_file, rule_config['rule']['language']):
                    print(f"XML rule successfully generated and validated: {xml_file}")
                    return xml_file
                else:
                    print("Generated rule failed validation - no violations found")
                    return None
                    
        except Exception as e:
            print(f"Error generating XML rule: {e}")
            return None 