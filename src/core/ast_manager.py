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

    def get_temp_file_extension(self, language: str) -> str:
        """
        Get file extension based on language
        """
        extensions = {
            'java': '.java',
            'python': '.py',
            'javascript': '.js',
            'typescript': '.ts',
            'ruby': '.rb',
            'go': '.go',
            'cpp': '.cpp',
            'c': '.c',
            'php': '.php',
            'scala': '.scala',
            'kotlin': '.kt',
            'xml': '.xml',
            'yaml': '.yml',
            'json': '.json'
        }
        return extensions.get(language.lower(), '.txt')

    def generate_ast(self, code: str, language: str) -> Optional[Dict]:
        """
        Generate AST using PMD via podman
        """
        try:
            # Create temporary file with proper extension
            ext = self.get_temp_file_extension(language)
            temp_file = self.temp_dir / f"temp{ext}"
            
            # Write code to temp file
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(code)

            # Run PMD AST dump via podman
            result = subprocess.run([
                'podman', 'run', '--rm',
                '-v', f"{temp_file.parent}:/src",
                'docker.io/lobocode/pmd:7.10.0',
                'ast-dump',
                '--file', f"src/{temp_file.name}",
                f"-l={language}",
                '-e=UTF-8'
            ], capture_output=True, text=True)

            if result.returncode != 0:
                print(f"Error generating AST: {result.stderr}")
                return None

            # Parse AST output
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                print("Error parsing AST output")
                return None

        except Exception as e:
            print(f"Error in AST generation: {e}")
            return None
        finally:
            # Cleanup temp file
            if temp_file.exists():
                temp_file.unlink()

    def analyze_examples(self, rule_config: Dict) -> Dict:
        """
        Analyze good and bad examples from rule configuration
        """
        language = rule_config['language']
        good_example = rule_config['examples']['good']
        bad_example = rule_config['examples']['bad']

        # Use cache if enabled
        if self.use_cache:
            good_cache = self.get_cache_path(good_example, language)
            bad_cache = self.get_cache_path(bad_example, language)
            
            if good_cache.exists() and bad_cache.exists():
                return {
                    'good_ast': json.loads(good_cache.read_text()),
                    'bad_ast': json.loads(bad_cache.read_text())
                }

        # Generate ASTs
        good_ast = self.generate_ast(good_example, language)
        bad_ast = self.generate_ast(bad_example, language)

        # Cache results if enabled
        if self.use_cache and good_ast and bad_ast:
            good_cache = self.get_cache_path(good_example, language)
            bad_cache = self.get_cache_path(bad_example, language)
            
            good_cache.write_text(json.dumps(good_ast))
            bad_cache.write_text(json.dumps(bad_ast))

        return {
            'good_ast': good_ast,
            'bad_ast': bad_ast
        } 