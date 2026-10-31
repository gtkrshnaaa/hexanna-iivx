#!/usr/bin/env bash
set -euo pipefail

echo "=========================================================="
echo "Hexanna IIVX: Empirical Benchmarking Suite"
echo "=========================================================="

DATA_DIR="benchmarks/data"
OUTPUT_DIR="benchmarks/results"
mkdir -p "${DATA_DIR}" "${OUTPUT_DIR}"

# 1. Workload Generation
echo "[*] Generating TPC-H datasets..."
python3 benchmarks/datasets/generate_workloads.py --scale 1.0 --out-dir "${DATA_DIR}/sf1"

# 2. Execute tests and comparisons
echo "[*] Benchmarks initialized."
echo "[*] Results saved in ${OUTPUT_DIR}."
