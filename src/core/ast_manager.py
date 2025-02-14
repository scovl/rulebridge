from pathlib import Path
from typing import Dict, List, Optional
import json
import random
import tempfile
import subprocess

class ASTManager:
    def __init__(self, max_samples: int = 3, max_ast_size: int = 50000):
        self.max_samples = max_samples
        self.max_ast_size = max_ast_size
        self.temp_dir = Path(tempfile.mkdtemp())

    def collect_relevant_asts(self, project_path: str, rule_context: Dict) -> Dict:
        """
        Collect relevant ASTs based on rule context and examples
        """
        # 1. First get AST from bad example
        bad_example_ast = self.get_ast_from_code(rule_context['examples']['bad'])
        
        # 2. Find similar patterns in project
        similar_files = self.find_similar_patterns(project_path, bad_example_ast)
        
        # 3. Sample most relevant ASTs
        selected_asts = self.sample_relevant_asts(similar_files)
        
        return {
            'example_ast': bad_example_ast,
            'project_samples': selected_asts
        }

    def find_similar_patterns(self, project_path: str, example_ast: Dict) -> List[Path]:
        """
        Find files with similar AST patterns to the example
        """
        similar_files = []
        pattern_signature = self.get_ast_signature(example_ast)
        
        for file_path in Path(project_path).rglob('*.java'):
            file_ast = self.get_ast_from_file(file_path)
            if self.has_similar_pattern(file_ast, pattern_signature):
                similar_files.append(file_path)
        
        return similar_files

    def sample_relevant_asts(self, files: List[Path]) -> List[Dict]:
        """
        Sample most relevant ASTs, keeping total size manageable
        """
        samples = []
        current_size = 0
        
        # Sort files by relevance/size
        sorted_files = self.sort_by_relevance(files)
        
        for file in sorted_files:
            ast = self.get_ast_from_file(file)
            ast_size = len(json.dumps(ast))
            
            if current_size + ast_size > self.max_ast_size:
                break
                
            if len(samples) >= self.max_samples:
                break
                
            samples.append(ast)
            current_size += ast_size
        
        return samples 

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