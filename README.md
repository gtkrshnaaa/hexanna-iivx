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

Run the universal installer to build and register the `hexanna` command in your OS PATH, enabling execution from any directory:

```bash
./install.sh
```

Installer options:
- `./install.sh`: Automatically detects privileges and installs to `~/.local/bin/hexanna` (or `/usr/local/bin/hexanna` if root).
- `./install.sh --user`: Force install to user directory (`~/.local/bin/hexanna`).
- `sudo ./install.sh --system`: Force install to system binary directory (`/usr/local/bin/hexanna`).
- `./install.sh --uninstall`: Remove the installed launcher.

For local Python virtual environment development:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[all]"
```

### Interactive TUI REPL

Launch the interactive REPL from any directory in your terminal:

```bash
hexanna
# or explicitly:
hexanna repl
```

Available REPL commands:
- `/inspect <path>`: View structural metadata and relational schema tables.
- `/profile <path> <column>`: Compute statistical sketches and null distributions.
- `/sql <query> [-> out.parquet]`: Preview analytical SQL in terminal or stream out-of-core to disk.
- `/run <objective>`: Launch the autonomous ReAct agent loop for a goal.
- `/sessions`: List historical chat sessions stored in the SQLite database.
- `/history [limit]`: Display recent interactive command history from SQLite.
- `/history-chat [session_id]`: Display message turns for a chat session from SQLite.
- `/clear-history`: Purge all historical chat sessions and commands in SQLite.
- `/artifacts [limit]`: List generated out-of-core dataset artifacts in SQLite.
- `/memory`: Inspect process RSS, VMS, CPU, and DuckDB disk spill metrics.
- `/config`: Inspect or update model, base URL, and memory ceilings stored in SQLite.
- `/help`: Display the commands reference table.

### CLI Commands

Inspect recent interactive command history from SQLite:

```bash
hexanna history --limit 20
```

List historical sessions from SQLite:

```bash
hexanna sessions --limit 20
```

List persisted artifacts from SQLite:

```bash
hexanna artifacts --limit 20
```

Inspect a dataset schema without loading records into memory:

```bash
hexanna inspect "data/sample.parquet"
```

Calculate statistical sketches for a column:

```bash
hexanna profile "data/sample.parquet" "column_name"
```

Execute an out-of-core analytical transformation directly to disk:

```bash
hexanna query "SELECT category, SUM(price) FROM 'data/sales.parquet' GROUP BY category" "output/summary.parquet"
```

Run an autonomous goal:

```bash
export LLM_API_KEY="your-api-key"
export LLM_BASE_URL="https://api.groq.com/openai/v1"
hexanna run "Aggregate all lineitems grouped by return flag and save to output/flag_summary.parquet"
```

## Running Benchmarks

```bash
bash benchmarks/run_benchmarks.sh
```

## License

MIT
