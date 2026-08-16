#!/usr/bin/env bash
# Fetch the external tooling the battery depends on.
# ROBOT is used only for the three OWL checks (SAR-L01 to SAR-L03); every other
# check runs in rdflib and needs nothing but pip install -r requirements.txt.
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p tools

if [ ! -f tools/robot.jar ]; then
  echo "Fetching ROBOT..."
  curl -sSL -o tools/robot.jar \
    https://github.com/ontodev/robot/releases/latest/download/robot.jar
fi

if ! command -v java >/dev/null 2>&1; then
  echo "WARNING: no java on PATH. SAR-L01 to SAR-L03 will report cantTell."
  echo "         On macOS: brew install openjdk"
else
  java -jar tools/robot.jar --version
fi

echo "Setup complete."
