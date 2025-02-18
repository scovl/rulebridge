from pathlib import Path
from typing import Dict, Optional
import subprocess
import json

class PMDAnalyzer:
    def analyze(self, rule_file: Path, source_path: Path, language: str) -> Optional[Dict]:
        """
        Analyze source code using PMD rule via podman
        
        Args:
            rule_file: Path to PMD rule XML
            source_path: Path to source code to analyze
            language: Programming language to analyze
        """
        try:
            result = subprocess.run([
                'podman', 'run', '--rm',
                '-v', f"{source_path.parent}:/src",
                '-v', f"{rule_file.parent}:/rules",
                'docker.io/lobocode/pmd:7.10.0',
                'check',
                '-R', f"/rules/{rule_file.name}",
                '-d', f"src/{source_path.name}",
                f"-l={language}",
                '-f', 'json'
            ], capture_output=True, text=True)

            if result.returncode != 0:
                print(f"Error running PMD check: {result.stderr}")
                return None

            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                print("Error parsing PMD output")
                return None

        except Exception as e:
            print(f"Error during analysis: {e}")
            return None 