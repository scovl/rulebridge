# Rule Bridge

A bridge between natural language rule descriptions and static code analysis tools.

## Overview

This project converts natural language rule descriptions into static analysis rules, currently supporting:
- PMD (experimental)

Planned support for:
- Semgrep
- SonarQube Custom Rules
- Other static analysis engines

## How it Works

1. Takes a natural language rule description via `entryPoint.json`
2. Generates AST of the target code using PMD's --dump-ast
3. Uses AI with AST context to generate accurate XPath expressions
4. Converts the rule into PMD XML format
5. Validates and executes the rule

## Architecture

```
rulebridge/
├── src/
│   ├── core/          # Core rule processing
│   ├── utils/         # Utility functions
│   └── config/        # Configuration
├── examples/          # Example rules
└── tests/            # Test suite
```

## Current Support (Experimental)

- PMD XPath Rules
  - XML validation
  - Rule generation
  - Basic rule testing

## Planned Extensions

- Semgrep Rules
  - YAML format
  - Pattern matching
  - Multiple language support

- SonarQube Custom Rules
  - JSON format
  - Quality profiles
  - Issue tracking

- Additional Engines
  - ESLint
  - Checkstyle
  - SpotBugs

## Usage

### Using with Podman
```bash
# Start PMD container
podman-compose up -d

# Run analysis
./analyze.sh rule.xml <source_code_path>

# Stop container when done
podman-compose down
```

### Manual Setup
```bash
# Configure settings
Edit src/config/settings.py

# Create rule description
Edit entryPoint.json

# Generate and test rule
python main.py
```

## Note

The PMD integration is currently experimental and serves as a proof of concept. The project's goal is to support multiple static analysis engines, with Semgrep being the next planned integration.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. Areas of interest:
- Additional engine support
- Rule validation improvements
- AI prompt engineering
- Test coverage

## License

MIT

## Advanced Features

### AST-Aware Rule Generation
- Uses PMD's Abstract Syntax Tree
- Provides structural context to AI
- Improves XPath expression accuracy
- Better pattern matching