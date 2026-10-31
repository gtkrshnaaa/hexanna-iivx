import os
import argparse
import duckdb

def generate_tpch_dataset(target_dir: str, scale_factor: float):
    """
    Generates deterministic TPC-H relational benchmark tables using embedded DuckDB.
    Scale Factor (SF) 1.0 ~ 1 GB raw, SF 5.0 ~ 5 GB, SF 10.0 ~ 10 GB.
    """
    os.makedirs(target_dir, exist_ok=True)
    conn = duckdb.connect()
    print(f"[*] Generating TPC-H dataset with Scale Factor {scale_factor} in {target_dir}...")

    conn.execute(f"CALL dbgen(sf = {scale_factor});")
    tables = ["lineitem", "orders", "customer", "part", "supplier"]

    for tbl in tables:
        out_file = os.path.join(target_dir, f"{tbl}.parquet")
        conn.execute(f"COPY {tbl} TO '{out_file}' (FORMAT PARQUET, COMPRESSION ZSTD);")
        size_mb = os.path.getsize(out_file) / (1024 * 1024)
        print(f"    - Persisted: {out_file} ({size_mb:.2f} MB)")

    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate TPC-H workloads")
    parser.add_argument("--scale", type=float, default=1.0, help="TPC-H Scale factor (e.g. 1.0, 5.0, 10.0)")
    parser.add_argument("--out-dir", type=str, default="benchmarks/data/sf1", help="Target directory")
    args = parser.parse_args()
    generate_tpch_dataset(args.out_dir, scale_factor=args.scale)
