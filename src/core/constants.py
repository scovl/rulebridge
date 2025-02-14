# PMD Rule XML constants
PMD_RULE_METADATA = {
    'RULESET_NAME': 'Custom PMD Rules',
    'RULESET_XMLNS': 'http://pmd.sourceforge.net/ruleset/2.0.0',
    'RULESET_XSI': 'http://www.w3.org/2001/XMLSchema-instance',
    'RULESET_SCHEMA_LOCATION': 'http://pmd.sourceforge.net/ruleset/2.0.0 http://pmd.sourceforge.net/ruleset_2_0_0.xsd',
    'RULE_CLASS': 'net.sourceforge.pmd.lang.rule.XPathRule'
}

# Mapping between PMD severity levels and Sonarqube format
PMD_SONAR_MAPPING = {
    # PMD severity to Sonar severity
    'SEVERITY': {
        1: 'BLOCKER',
        2: 'CRITICAL',
        3: 'MAJOR',
        4: 'MINOR',
        5: 'INFO'
    },
    # PMD description tag to Sonar type and debt
    'DESCRIPTION_TAG': {
        '[CODE_SMELL]': {
            'type': 'CODE_SMELL',
            'debt': '20min'
        },
        '[BUG]': {
            'type': 'BUG',
            'debt': '30min'
        },
        '[VULNERABILITY]': {
            'type': 'VULNERABILITY',
            'debt': '45min'
        },
        '[SECURITY_HOTSPOT]': {
            'type': 'SECURITY_HOTSPOT',
            'debt': '45min'
        }
    },
    # PMD description number to Sonar effort
    'EFFORT': {
        '[100]': '100min',
        '[50]': '50min',
        '[20]': '20min',
        '[10]': '10min',
        '[5]': '5min'
    }
}

# Combined tags for PMD description field
SEVERITY_TYPE_TAGS = {
    1: '[BLOCKER][100]',
    2: '[CRITICAL][50]',
    3: '[CODE_SMELL][20]',
    4: '[MINOR][10]',
    5: '[INFO][5]'
} 