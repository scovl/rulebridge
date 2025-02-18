#!/bin/bash

# Create project directories
mkdir -p .ast_cache
mkdir -p test/src

# Pull PMD image
podman pull docker.io/lobocode/pmd:7.10.0

# Verify image
if ! podman image exists docker.io/lobocode/pmd:7.10.0; then
    echo "Error: Failed to pull PMD image"
    exit 1
fi

echo "Setup completed successfully" 