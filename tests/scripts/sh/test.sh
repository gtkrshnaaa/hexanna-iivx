#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$REPO_DIR"

echo "=========================================================="
echo "Hexanna IIVX: Test Suite Runner"
echo "=========================================================="

if [ -f ".env.local" ]; then
    set -a
    # shellcheck disable=SC1091
    source ".env.local"
    set +a
fi

if command -v pytest >/dev/null 2>&1; then
    pytest tests/
elif command -v docker >/dev/null 2>&1; then
    echo "[*] Host pytest not detected. Executing inside isolated container..."
    docker run --rm \
        --network host \
        --memory="2g" \
        --cpus="2" \
        -e PYTHONDONTWRITEBYTECODE=1 \
        -e DEEPSEEK_BASE_URL="${DEEPSEEK_BASE_URL:-}" \
        -e DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY:-}" \
        -e DEEPSEEK_MODEL="${DEEPSEEK_MODEL:-}" \
        -e GEMINI_BASE_URL="${GEMINI_BASE_URL:-}" \
        -e GEMINI_API_KEY="${GEMINI_API_KEY:-}" \
        -e GEMINI_MODEL="${GEMINI_MODEL:-}" \
        -v "$REPO_DIR":/app \
        -v /tmp/hexanna-pip-cache:/root/.cache/pip \
        -w /app \
        python:3.11-slim \
        bash -c "pip install -e '.[all]' >/dev/null 2>&1 && pytest tests/ -v"
else
    echo "[-] Neither pytest nor docker is available to run tests."
    exit 1
fi
