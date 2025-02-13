import json
from pathlib import Path
from typing import Optional, Dict, Any

class FileHandler:
    def read_json(self, file_path: Path) -> Optional[Dict]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao ler arquivo JSON: {e}")
            return None
    
    def write_xml(self, content: str, file_path: Path) -> bool:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Erro ao escrever arquivo XML: {e}")
            return False

    def read_sarif(self, file_path: Path) -> Optional[Dict]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao ler arquivo SARIF: {e}")
            return None 