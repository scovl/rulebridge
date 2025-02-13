import json
import yaml
import requests
import subprocess
from xml.dom import minidom
from pathlib import Path
from typing import Optional, Dict, Any
from config import CLIENT_ID, CLIENT_KEY, REALM, PROXIES

class RuleBridge:
    """
    Classe responsável por fazer a ponte entre regras em linguagem natural,
    PMD e Sonarqube
    """
    
    def __init__(self, yaml_file: str = "entryPoint.yaml") -> None:
        """
        Inicializa o RuleBridge.

        Args:
            yaml_file: Caminho para o arquivo YAML de entrada
        """
        self.yaml_file = yaml_file
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {CLIENT_KEY}',
            'X-Client-Id': CLIENT_ID,
            'X-Realm': REALM
        }
    
    def map_pmd_severity_to_sonar(self, pmd_severity):
        """
        Mapeia a severidade do PMD para o formato do Sonarqube
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
        Converte uma regra do PMD para o formato do Sonarqube 9.9 LTS
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
        Salva as regras no formato do Sonarqube 9.9 LTS
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
                
            print(f"Arquivo de regras salvo com sucesso em: {output_file}")
            
        except Exception as e:
            print(f"Erro ao salvar arquivo de regras: {str(e)}")
            return None

    def convert_pmd_to_sonar(self, pmd_report):
        """
        Converte o relatório PMD no formato serif para o formato JSON do Sonarqube
        """
        sonar_issues = []
        
        try:
            # Converte cada violação do PMD para o formato do Sonarqube
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
            print(f"Erro ao converter o relatório: {str(e)}")
            return None

    def process_natural_language_rule(self):
        """
        Processa a regra em linguagem natural e converte para XML do PMD
        usando o Stackspot como intermediário
        """
        try:
            # Lê o arquivo YAML
            with open(self.yaml_file, 'r', encoding='utf-8') as f:
                rule_config = yaml.safe_load(f)
            
            # Primeiro prompt para gerar o XPath
            xpath_prompt = f"""
            Crie uma expressão XPath para PMD que implemente a seguinte regra:
            
            Descrição: {rule_config['rule']['what_to_find']}
            
            A expressão deve ser válida para o PMD e detectar o problema mostrado no exemplo ruim:
            
            Código com problema:
            {rule_config['rule']['examples']['bad']}
            
            Código correto:
            {rule_config['rule']['examples']['good']}
            
            Retorne APENAS a expressão XPath, sem explicações.
            """
            
            # Chama Stackspot para gerar o XPath
            xpath_payload = {
                'prompt': xpath_prompt,
                'temperature': 0.3,
                'max_tokens': 500
            }
            
            xpath_response = requests.post(
                'URL_DO_STACKSPOT/completions',
                headers=self.headers,
                json=xpath_payload,
                proxies=PROXIES
            )
            
            if xpath_response.status_code != 200:
                print(f"Erro ao gerar XPath: {xpath_response.status_code}")
                return None
            
            xpath_expression = xpath_response.json()['choices'][0]['text'].strip()
            
            # Agora gera o XML completo com o XPath
            xml_prompt = f"""
            Crie uma regra PMD XML com a seguinte estrutura exata:
            
            <?xml version="1.0"?>
            <ruleset name="Custom Rules"
                xmlns="http://pmd.sourceforge.net/ruleset/2.0.0"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xsi:schemaLocation="http://pmd.sourceforge.net/ruleset/2.0.0 https://pmd.sourceforge.io/ruleset_2_0_0.xsd">
                
                <description>Regra customizada gerada via IA</description>
                
                <rule name="{rule_config['rule']['name']}"
                      language="{rule_config['rule']['language']}"
                      message="{rule_config['rule']['description']}"
                      class="net.sourceforge.pmd.lang.rule.XPathRule"
                      externalInfoUrl="https://pmd.github.io/latest/pmd_rules_java.html">
                      
                    <description>{rule_config['rule']['description']}</description>
                    <priority>{rule_config['rule']['severity']}</priority>
                    <properties>
                        <property name="xpath">
                            <value>
                            <![CDATA[
                            {xpath_expression}
                            ]]>
                            </value>
                        </property>
                    </properties>
                    <example>
                        <![CDATA[
                        // Exemplo de código correto
                        {rule_config['rule']['examples']['good']}
                        
                        // Exemplo de código incorreto
                        {rule_config['rule']['examples']['bad']}
                        ]]>
                    </example>
                </rule>
            </ruleset>
            """
            
            payload = {
                'prompt': xml_prompt,
                'temperature': 0.3,
                'max_tokens': 1000
            }
            
            response = requests.post(
                'URL_DO_STACKSPOT/completions',
                headers=self.headers,
                json=payload,
                proxies=PROXIES
            )
            
            if response.status_code == 200:
                xml_string = response.json()['choices'][0]['text']
                
                # Parse e formata o XML usando minidom
                xml_dom = minidom.parseString(xml_string)
                pretty_xml = xml_dom.toprettyxml(indent="  ")
                
                # Salva a regra XML formatada
                xml_file = Path(self.yaml_file).with_suffix('.xml')
                with open(xml_file, 'w', encoding='utf-8') as f:
                    f.write(pretty_xml)
                
                # Valida o XML gerado
                if self.validate_pmd_rule(xml_file):
                    print(f"Regra XML gerada com sucesso: {xml_file}")
                    return xml_file
                else:
                    print("XML gerado não é válido para o PMD")
                    return None
                
            else:
                print(f"Erro na chamada ao Stackspot: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Erro ao processar regra: {str(e)}")
            return None

    def validate_pmd_rule(self, xml_file):
        """
        Valida se o arquivo XML está no formato correto do PMD
        """
        try:
            dom = minidom.parse(xml_file)
            
            # Verifica elementos obrigatórios
            ruleset = dom.getElementsByTagName('ruleset')
            if not ruleset:
                raise ValueError("Elemento 'ruleset' não encontrado")
            
            rule = dom.getElementsByTagName('rule')
            if not rule:
                raise ValueError("Elemento 'rule' não encontrado")
            
            # Verifica atributos obrigatórios
            required_attrs = ['name', 'language', 'message', 'class']
            for attr in required_attrs:
                if not rule[0].getAttribute(attr):
                    raise ValueError(f"Atributo '{attr}' não encontrado na regra")
            
            # Verifica elementos obrigatórios dentro da regra
            required_elements = ['description', 'priority']
            for elem in required_elements:
                if not rule[0].getElementsByTagName(elem):
                    raise ValueError(f"Elemento '{elem}' não encontrado na regra")
            
            return True
            
        except Exception as e:
            print(f"Erro na validação do XML: {str(e)}")
            return False

    def execute_pmd_command(self, xml_rule: Path, source_path: str) -> Optional[Path]:
        """
        Executa o comando PMD CLI.

        Args:
            xml_rule: Caminho para o arquivo de regra XML
            source_path: Caminho para o código fonte a ser analisado

        Returns:
            Path do arquivo SARIF gerado ou None em caso de erro
        """
        output_file = Path('output.sarif')
        try:
            cmd = [
                'pmd',
                '-R', str(xml_rule),
                '-d', source_path,
                '-f', 'sarif',
                '-r', str(output_file)
            ]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return output_file
        except subprocess.CalledProcessError as e:
            print(f"Erro ao executar PMD: {e}")
            return None

    def read_sarif_file(self, sarif_file: Path) -> Optional[Dict[str, Any]]:
        """
        Lê o arquivo SARIF gerado pelo PMD.

        Args:
            sarif_file: Caminho para o arquivo SARIF

        Returns:
            Dicionário com o conteúdo do arquivo ou None em caso de erro
        """
        try:
            with open(sarif_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao ler arquivo SARIF: {e}")
            return None

    def process(self) -> None:
        """
        Executa o fluxo de processamento para gerar a regra XML.
        """
        try:
            # 1. Processar regra em linguagem natural
            xml_rule = self.process_natural_language_rule()
            if not xml_rule:
                return

            print(f"Regra XML gerada com sucesso. Execute agora:")
            print(f"./analyze.sh {xml_rule} <caminho_do_codigo_fonte>")

        except Exception as e:
            print(f"Erro durante a execução: {e}")

def main() -> None:
    """Função principal que instancia e executa o RuleBridge."""
    bridge = RuleBridge()
    bridge.process()

if __name__ == "__main__":
    main() 