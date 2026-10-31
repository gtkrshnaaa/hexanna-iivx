# Hexanna IIVX

A deterministic, metadata-driven agent harness engineered for out-of-core local data engineering on commodity workstations without context saturation or host memory exhaustion.

## Key Architectural Principles

1. Zero Raw-Payload Transmission: Remote reasoning models only receive statistical sketches, schemas, and null distributions. Raw records never traverse network boundaries.
2. Deterministic Sandboxed Tools: Arbitrary terminal shell execution is replaced by typed, functional operations mapped to schema contracts.
3. Hard Memory Caps and Disk Spills: Local embedded DuckDB instances clamp heap allocations (default 2GB) and stream directly to disk Parquet files.

## Project Structure

```text
hexanna-iivx/
├── config/
│   ├── default.toml                    # Default hardware memory limits and engine settings
│   └── logging.yaml                    # Structured telemetry logs
├── src/
│   └── hexanna/
│       ├── __main__.py                 # CLI interface
│       ├── domain/                     # Entities, exceptions, and resource policies
│       ├── ports/                      # Abstract protocols (IDataEngine, ILLMGateway, ITelemetry)
│       ├── adapters/                   # DuckDB engine, OpenAI client, psutil tracker
│       ├── harness/                    # ReAct runtime, context builder, dispatcher
│       └── tools/                      # Schema inspector, out-of-core SQL, profile sketcher
├── tests/
│   ├── unit/                           # Isolated unit tests
│   └── integration/                    # End-to-end pipeline execution tests
├── benchmarks/
│   ├── datasets/                       # TPC-H data generation scripts
│   ├── baselines/                      # In-memory pandas and shell agent baselines
│   ├── profiling/                      # C-level memory daemon tracker
│   └── analysis/                       # LaTeX vector plot generator
├── paper/                              # Reproducible LaTeX manuscript and figures
├── pyproject.toml                      # Modern packaging configuration
└── Dockerfile                          # Containerized execution environment
```

## Quick Start

### Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[all]"
```

### Interactive TUI REPL

Launch the interactive REPL with real-time memory metrics, tab auto-completion, and out-of-core streaming:

```bash
python3 -m hexanna
# or explicitly:
python3 -m hexanna repl
```

Available REPL commands:
- `/inspect <path>`: View structural metadata and relational schema tables.
- `/profile <path> <column>`: Compute statistical sketches and null distributions.
- `/sql <query> [-> out.parquet]`: Preview analytical SQL in terminal or stream out-of-core to disk.
- `/run <objective>`: Launch the autonomous ReAct agent loop for a goal.
- `/memory`: Inspect process RSS, VMS, CPU, and DuckDB disk spill metrics.
- `/config`: Inspect or update model, base URL, and memory ceilings.
- `/help`: Display the commands reference table.

### CLI Commands

Inspect a dataset schema without loading records into memory:

```bash
python3 -m hexanna inspect "data/sample.parquet"
```

Calculate statistical sketches for a column:

```bash
python3 -m hexanna profile "data/sample.parquet" "column_name"
```

Execute an out-of-core analytical transformation directly to disk:

```bash
python3 -m hexanna query "SELECT category, SUM(price) FROM 'data/sales.parquet' GROUP BY category" "output/summary.parquet"
```

Run an autonomous goal:

```bash
export LLM_API_KEY="your-api-key"
export LLM_BASE_URL="https://api.groq.com/openai/v1"
python3 -m hexanna run "Aggregate all lineitems grouped by return flag and save to output/flag_summary.parquet"
```

## Running Benchmarks

```bash
bash benchmarks/run_benchmarks.sh
```

## License

Apache-2.0
