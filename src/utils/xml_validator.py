from pathlib import Path
from typing import Union, Optional
import tempfile
from src.core.analyzer import PMDAnalyzer

class XMLValidator:
    def validate_pmd_rule(self, xml_file: Union[str, Path], language: str) -> bool:
        """
        Validate PMD rule by testing it against a bad example
        """
        try:
            # Create temporary test file with known violation
            with tempfile.NamedTemporaryFile(suffix=f'.{language}', mode='w', delete=False) as tmp:
                tmp.write(self.get_test_code(language))
                test_file = Path(tmp.name)

            # Run PMD analysis
            analyzer = PMDAnalyzer()
            result = analyzer.analyze(
                rule_file=Path(xml_file),
                source_path=test_file,
                language=language
            )

            # Rule is valid if it finds at least one violation
            return result is not None and len(result.get('violations', [])) > 0

        except Exception as e:
            print(f"Error validating rule: {e}")
            return False
        finally:
            if 'test_file' in locals():
                test_file.unlink(missing_ok=True)

    def get_test_code(self, language: str) -> str:
        """Get test code that should trigger the rule"""
        return self.test_cases.get(language, "")

    test_cases = {
        'java': 'public class Test { public void test() { } public void test() { } }',
        'xml': '<project><dependencies></dependencies></project>',
        'python': 'def test():\n    pass\ndef test():\n    pass'
    } 