#!/usr/bin/env bash
set -e

# This script runs the Python scraper.
# Dependencies are expected to be installed by the GitHub Actions workflow.

echo "Running Python scraper..."
python3 scrape.py
