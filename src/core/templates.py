from .constants import PMD_RULE_METADATA, SEVERITY_MAPPING

class XMLTemplates:
    XML_HEADER = f"""<?xml version="1.0" encoding="UTF-8"?>
<ruleset name="{PMD_RULE_METADATA['RULESET_NAME']}"
         xmlns="{PMD_RULE_METADATA['RULESET_XMLNS']}"
         xmlns:xsi="{PMD_RULE_METADATA['RULESET_XSI']}"
         xsi:schemaLocation="{PMD_RULE_METADATA['RULESET_SCHEMA_LOCATION']}">"""

    XML_FOOTER = """
</ruleset>"""

    RULE_TEMPLATE = """
    <rule name="{name}"
          language="{language}"
          message="{message}"
          class="{rule_class}">
        <description>{severity_tag}</description>
        <priority>{severity}</priority>
        <properties>
            <property name="xpath">
                <value>
                {xpath}
                </value>
            </property>
        </properties>
    </rule>""" 