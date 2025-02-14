from pathlib import Path
from typing import Dict, Optional
import jpype
import json

class PMDAnalyzer:
    def __init__(self):
        self.PMD = jpype.JClass('net.sourceforge.pmd.PMD')
        self.PMDConfiguration = jpype.JClass('net.sourceforge.pmd.PMDConfiguration')
        
    def analyze(self, rule_file: Path, source_path: Path) -> Dict:
        """
        Analyze source code using PMD rule
        
        Args:
            rule_file: Path to PMD rule XML
            source_path: Path to source code to analyze
            
        Returns:
            Analysis results as dictionary
        """
        try:
            # Configure PMD
            config = self.PMDConfiguration()
            config.setInputPaths(str(source_path))
            config.setRuleSets(str(rule_file))
            config.setReportFormat("json")
            
            # Run analysis
            pmd = self.PMD()
            results = pmd.runPmd(config)
            
            return self._convert_results(results)
            
        except Exception as e:
            print(f"Error during analysis: {e}")
            return None
            
    def _convert_results(self, pmd_results) -> Dict:
        """Convert PMD results to dictionary format"""
        return {
            'violations': [
                {
                    'rule': violation.getRule().getName(),
                    'description': violation.getDescription(),
                    'file': violation.getFilename(),
                    'line': violation.getBeginLine(),
                    'priority': violation.getRule().getPriority()
                }
                for violation in pmd_results.getViolations()
            ]
        } 