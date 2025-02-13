class XMLTemplates:
    XML_HEADER = """<?xml version="1.0"?>
<ruleset name="Custom Rules"
    xmlns="http://pmd.sourceforge.net/ruleset/2.0.0"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://pmd.sourceforge.net/ruleset/2.0.0 https://pmd.sourceforge.io/ruleset_2_0_0.xsd">
    
    <description>Custom rule generated via AI</description>"""

    XML_FOOTER = """
</ruleset>"""

    RULE_TEMPLATE = """
    <rule name="{name}"
          language="{language}"
          message="{message}"
          class="net.sourceforge.pmd.lang.rule.XPathRule"
          externalInfoUrl="https://pmd.github.io/latest/pmd_rules_java.html">
          
        <description>{description}</description>
        <priority>{severity}</priority>
        <properties>
            <property name="xpath">
                <value>
                <![CDATA[
                {xpath}
                ]]>
                </value>
            </property>
        </properties>
        <example>
            <![CDATA[
            // Good code example
            {good_example}
            
            // Bad code example
            {bad_example}
            ]]>
        </example>
    </rule>""" 