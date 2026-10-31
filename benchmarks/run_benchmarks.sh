#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

echo "=========================================================="
echo "Hexanna IIVX: Empirical Benchmarking Suite"
echo "=========================================================="

DATA_DIR="benchmarks/data"
OUTPUT_DIR="benchmarks/results"
FIGURES_DIR="paper/figures"
TABLES_DIR="paper/tables"
mkdir -p "${DATA_DIR}" "${OUTPUT_DIR}" "${FIGURES_DIR}" "${TABLES_DIR}"

# 1. Workload Generation (SF-1 sample check)
if [ ! -f "${DATA_DIR}/sf1/lineitem.parquet" ]; then
    echo "[*] Synthesizing TPC-H SF-1 baseline tables..."
    python3 benchmarks/datasets/generate_workloads.py --scale 1.0 --out-dir "${DATA_DIR}/sf1" || true
fi

# 2. Execute Orchestrator
echo "[*] Executing multi-system benchmark matrix (Hexanna vs Polars vs Raw DuckDB vs Pandas)..."
python3 benchmarks/orchestrator.py

# 3. Generate LaTeX plots & publication figures
echo "[*] Generating publication plots and LaTeX tables..."
python3 benchmarks/analysis/generate_latex_plots.py

echo "[OK] Benchmark execution complete. Artifacts written to ${OUTPUT_DIR}, ${FIGURES_DIR}, and ${TABLES_DIR}."
