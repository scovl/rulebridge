from pathlib import Path
from typing import Dict, List, Optional
import json
import random

class ASTManager:
    def __init__(self, max_samples: int = 3, max_ast_size: int = 50000):
        self.max_samples = max_samples
        self.max_ast_size = max_ast_size

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