#!/bin/bash

# Check if required arguments are provided
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <rule_xml> <source_path>"
    exit 1
fi

RULE_XML=$1
SOURCE_PATH=$2
OUTPUT_FILE="pmd_report.json"
AST_CACHE_DIR=".ast_cache"

# Create AST cache directory
mkdir -p $AST_CACHE_DIR

# Generate AST for bad example first
echo "Generating example AST..."
podman-compose run --rm pmd check \
    -d "examples/bad_example" \
    --dump-ast \
    -f json \
    -r "$AST_CACHE_DIR/example_ast.json"

# Smart AST sampling from project
echo "Sampling project ASTs..."
python src/tools/ast_sampler.py "$SOURCE_PATH" "$AST_CACHE_DIR"

# Run PMD analysis
echo "Running PMD analysis..."
podman-compose run --rm pmd check \
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