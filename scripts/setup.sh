#!/bin/bash

# Create lib directory
mkdir -p lib

# Download PMD dependencies
wget https://github.com/pmd/pmd/releases/download/pmd_releases%2F7.10.0/pmd-bin-7.10.0.zip
unzip pmd-bin-7.10.0.zip

# Copy PMD JARs
cp pmd-bin-7.10.0/lib/*.jar lib/

# Cleanup
rm -rf pmd-bin-7.10.0* 