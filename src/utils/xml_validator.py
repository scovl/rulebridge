from xml.dom import minidom
from typing import Union
from pathlib import Path

class XMLValidator:
    def validate_pmd_rule(self, xml_file: Union[str, Path]) -> bool:
        try:
            dom = minidom.parse(xml_file)
            
            # Validate root elements
            ruleset = dom.getElementsByTagName('ruleset')
            if not ruleset:
                raise ValueError("Element 'ruleset' not found")
            
            rule = dom.getElementsByTagName('rule')
            if not rule:
                raise ValueError("Element 'rule' not found")
            
            # Validate required attributes
            required_attrs = ['name', 'language', 'message', 'class']
            for attr in required_attrs:
                if not rule[0].getAttribute(attr):
                    raise ValueError(f"Attribute '{attr}' not found in rule")
            
            # Validate required child elements
            required_elements = ['description', 'priority']
            for elem in required_elements:
                if not rule[0].getElementsByTagName(elem):
                    raise ValueError(f"Element '{elem}' not found in rule")
            
            return True
            
        except Exception as e:
            print(f"Error validating XML: {e}")
            return False 