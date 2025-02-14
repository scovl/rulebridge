from pathlib import Path
from typing import Dict, Optional
import json
import tempfile
import hashlib
import jpype
import jpype.imports

class ASTManager:
    def __init__(self, use_cache: bool = False):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.use_cache = use_cache
        self.cache_dir = Path('.ast_cache') if use_cache else None
        
        if self.use_cache:
            self.cache_dir.mkdir(exist_ok=True)
            
        # Initialize JVM if not running
        if not jpype.isJVMStarted():
            jpype.startJVM(classpath=['./lib/pmd-core-7.10.0.jar'])
            
        # Import PMD classes
        self.PMDConfiguration = jpype.JClass('net.sourceforge.pmd.PMDConfiguration')
        self.LanguageRegistry = jpype.JClass('net.sourceforge.pmd.lang.LanguageRegistry')

    def get_cache_path(self, code: str, language: str) -> Path:
        """Get cache file path for given code"""
        code_hash = hashlib.md5(code.encode()).hexdigest()
        return self.cache_dir / f"{code_hash}.{language}.ast.json"

    def get_ast_from_example(self, code: str, language: str) -> Optional[Dict]:
        """
        Extract AST using PMD's Java API directly
        
        Args:
            code: Source code example
            language: Programming language from entryPoint.json
        """
        if self.use_cache:
            cache_file = self.get_cache_path(code, language)
            if cache_file.exists():
                with open(cache_file) as f:
                    return json.load(f)

        try:
            # Get language support from PMD registry
            lang_registry = self.LanguageRegistry.getInstance()
            lang = lang_registry.getLanguageByName(language)
            if not lang:
                print(f"Language not supported by PMD: {language}")
                return None

            lang_version = lang.getDefaultVersion()
            parser = lang.getParser(lang_version)
            
            # Parse code to AST
            ast = parser.parse(code)
            
            # Convert AST to dictionary
            ast_dict = self._convert_ast_to_dict(ast)
            
            # Cache if enabled
            if self.use_cache and ast_dict:
                cache_file = self.get_cache_path(code, language)
                with open(cache_file, 'w') as f:
                    json.dump(ast_dict, f, indent=2)
                    
            return ast_dict

        except Exception as e:
            print(f"Error processing {language} AST: {e}")
            return None

    def _convert_ast_to_dict(self, node) -> Dict:
        """
        Convert PMD AST node to dictionary
        """
        result = {
            'type': node.getClass().getSimpleName(),
            'image': node.getImage() if hasattr(node, 'getImage') else None,
        }
        
        children = []
        for child in node.children():
            children.append(self._convert_ast_to_dict(child))
            
        if children:
            result['children'] = children
            
        return result

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