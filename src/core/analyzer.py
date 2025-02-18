from pathlib import Path
from typing import Dict, Optional, List
import subprocess
import json
import shlex

class PMDAnalyzer:
    PMD_IMAGE = "docker.io/lobocode/pmd:7.10.0"
    
    def _build_check_command(self, rule_file: Path, source_path: Path, language: str) -> List[str]:
        """
        Build safe command list for PMD check
        """
        return [
            'podman',
            'run',
            '--rm',
            '-v',
            f"{source_path.parent}:/src:Z",
            '-v',
            f"{rule_file.parent}:/rules:Z",
            self.PMD_IMAGE,
            'check',
            '-R',
            f"/rules/{rule_file.name}",
            '-d',
            f"src/{source_path.name}",
            f"-l={shlex.quote(language)}",
            '-f',
            'json'
        ]

    def analyze(self, rule_file: Path, source_path: Path, language: str) -> Optional[Dict]:
        """
        Analyze source code using PMD rule via podman
        
        Args:
            rule_file: Path to PMD rule XML
            source_path: Path to source code to analyze
            language: Programming language to analyze
        """
        if not all(isinstance(x, (Path, str)) for x in [rule_file, source_path, language]):
            print("Invalid input types")
            return None

        try:
            # Build and run command
            cmd = self._build_check_command(rule_file, source_path, language)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False  # Don't raise exception on non-zero exit
            )

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