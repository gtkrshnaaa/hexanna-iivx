#!/usr/bin/env bash
set -euo pipefail

echo "=========================================================="
echo "Hexanna IIVX: Test Suite Runner"
echo "=========================================================="

if command -v pytest >/dev/null 2>&1; then
    pytest tests/
elif command -v docker >/dev/null 2>&1; then
    echo "[*] Host pytest not detected. Executing inside isolated container..."
    docker run --rm \
        --memory="2g" \
        --cpus="2" \
        -v "$PWD":/app \
        -w /app \
        python:3.11-slim \
        bash -c "pip install --no-cache-dir -e '.[all]' && pytest tests/"
else
    echo "[-] Neither pytest nor docker is available to run tests."
    exit 1
fi
