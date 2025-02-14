#!/bin/bash

# Check if required arguments are provided
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <rule_xml> <source_path>"
    exit 1
fi

RULE_XML=$1
SOURCE_PATH=$2
OUTPUT_FILE="pmd_report.json"

# Run PMD with check and report generation
pmd check \
    -R "$RULE_XML" \
    -d "$SOURCE_PATH" \
    -f json \
    -r "$OUTPUT_FILE"

# Check PMD exit code
if [ $? -eq 0 ]; then
    echo "PMD analysis completed successfully"
    echo "Report saved to: $OUTPUT_FILE"
else
    echo "PMD analysis failed"
    exit 1
fi