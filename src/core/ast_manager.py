from pathlib import Path
from typing import Dict, Optional, List
import json
import tempfile
import subprocess
import hashlib
import shlex

class ASTManager:
    PMD_IMAGE = "docker.io/lobocode/pmd:7.10.0"
    
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

    def _build_ast_command(self, temp_file: Path, language: str) -> List[str]:
        """
        Build safe command list for PMD AST dump
        """
        return [
            'podman',
            'run',
            '--rm',
            '-v',
            f"{temp_file.parent}:/src:Z",
            self.PMD_IMAGE,
            'ast-dump',
            '--file',
            f"src/{temp_file.name}",
            f"-l={shlex.quote(language)}",
            '-e=UTF-8'
        ]

    def generate_ast(self, code: str, language: str) -> Optional[Dict]:
        """
        Generate AST using PMD via podman
        """
        if not isinstance(code, str) or not isinstance(language, str):
            print("Invalid input types")
            return None

        try:
            # Create temporary file with proper extension
            ext = self.get_temp_file_extension(language)
            temp_file = self.temp_dir / f"temp{ext}"
            
            # Write code to temp file
            temp_file.write_text(code, encoding='utf-8')

            # Build and run command
            cmd = self._build_ast_command(temp_file, language)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False  # Don't raise exception on non-zero exit
            )

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
        Analyze bad example from rule configuration
        
        Args:
            rule_config: Rule configuration from entryPoint.json
            
        Returns:
            Dictionary with AST for bad example
        """
        language = rule_config['language']
        bad_example = rule_config['examples']['bad']

        # Use cache if enabled
        if self.use_cache:
            bad_cache = self.get_cache_path(bad_example, language)
            
            if bad_cache.exists():
                return {
                    'ast': json.loads(bad_cache.read_text())
                }

        # Generate AST
        ast = self.generate_ast(bad_example, language)

        # Cache result if enabled
        if self.use_cache and ast:
            bad_cache = self.get_cache_path(bad_example, language)
            bad_cache.write_text(json.dumps(ast))

        return {'ast': ast} 