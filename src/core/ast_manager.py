from pathlib import Path
from typing import Dict, Optional
import json
import tempfile
import subprocess

class ASTManager:
    def __init__(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def get_ast_from_example(self, code: str, language: str) -> Optional[Dict]:
        """
        Extract AST from example code using PMD
        
        Args:
            code: Source code example
            language: Programming language (java, xml, etc)
            
        Returns:
            AST dictionary or None if error
        """
        try:
            # Create temporary file with example code
            temp_file = self.temp_dir / f"example.{language}"
            with open(temp_file, 'w') as f:
                f.write(code)

            # Get AST using PMD
            ast_file = self.temp_dir / "ast.json"
            result = subprocess.run([
                "podman-compose", "run", "--rm", "pmd",
                "check",
                "-d", str(temp_file),
                "--dump-ast",
                "-f", "json",
                "-r", str(ast_file)
            ], capture_output=True)

            if result.returncode != 0:
                print(f"Error getting AST: {result.stderr.decode()}")
                return None

            # Read generated AST
            with open(ast_file) as f:
                return json.load(f)

        except Exception as e:
            print(f"Error processing example AST: {e}")
            return None
        finally:
            # Cleanup temporary files
            if temp_file.exists():
                temp_file.unlink()
            if ast_file.exists():
                ast_file.unlink()

    def analyze_examples(self, rule_config: Dict) -> Dict:
        """
        Analyze good and bad examples from rule configuration
        
        Args:
            rule_config: Rule configuration from entryPoint.json
            
        Returns:
            Dictionary with ASTs for both examples
        """
        language = rule_config['language']
        good_example = rule_config['examples']['good']
        bad_example = rule_config['examples']['bad']

        return {
            'good_ast': self.get_ast_from_example(good_example, language),
            'bad_ast': self.get_ast_from_example(bad_example, language)
        } 