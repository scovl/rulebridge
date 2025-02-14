from pathlib import Path
from typing import Dict, Optional
import json
import tempfile
import subprocess
import hashlib

class ASTManager:
    def __init__(self, use_cache: bool = False):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.use_cache = use_cache
        self.cache_dir = Path('.ast_cache') if use_cache else None
        
        if self.use_cache:
            self.cache_dir.mkdir(exist_ok=True)

    def get_cache_path(self, code: str, language: str) -> Path:
        """Get cache file path for given code"""
        code_hash = hashlib.md5(code.encode()).hexdigest()
        return self.cache_dir / f"{code_hash}.{language}.ast.json"

    def get_ast_from_example(self, code: str, language: str) -> Optional[Dict]:
        """
        Extract AST from example code using PMD
        
        Args:
            code: Source code example
            language: Programming language (java, xml, etc)
            
        Returns:
            AST dictionary or None if error
        """
        if self.use_cache:
            cache_file = self.get_cache_path(code, language)
            if cache_file.exists():
                with open(cache_file) as f:
                    return json.load(f)

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
                ast_result = json.load(f)

            # Cache result if enabled
            if self.use_cache and ast_result:
                cache_file = self.get_cache_path(code, language)
                with open(cache_file, 'w') as f:
                    json.dump(ast_result, f, indent=2)

            return ast_result

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