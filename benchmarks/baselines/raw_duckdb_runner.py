import os
import time
from typing import Dict, Any, Optional
import duckdb

class RawDuckDBBaseline:
    """
    Zero-LLM Direct DuckDB Engine Baseline.
    Executes identical vectorized SQL queries directly in native DuckDB to quantify
    Hexanna IIVX's architectural orchestration overhead (dispatcher, context builder, tool state).
    """

    def __init__(self, data_dir: str, memory_limit: str = "2GB", temp_directory: Optional[str] = None):
        self.data_dir = data_dir
        self.memory_limit = memory_limit
        self.temp_directory = temp_directory or os.getenv("HEXANNA_TEMP_DIR", os.path.expanduser("~/.hexanna_tmp"))
        os.makedirs(self.temp_directory, exist_ok=True)

        self._conn = duckdb.connect(database=":memory:")
        self._conn.execute(f"SET max_memory = '{self.memory_limit}';")
        self._conn.execute(f"SET temp_directory = '{self.temp_directory}';")
        self._conn.execute("SET preserve_insertion_order = false;")

    def run_profile_a_scan_agg(self, output_path: str) -> Dict[str, Any]:
        """TPC-H Q6 Forecasting Revenue Change Query."""
        lineitem_p = os.path.join(self.data_dir, "lineitem.parquet")
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        query = f"""
        COPY (
            SELECT
                sum(l_extendedprice * l_discount) as revenue
            FROM '{lineitem_p}'
            WHERE
                l_shipdate >= DATE '1994-01-01'
                AND l_shipdate < DATE '1995-01-01'
                AND l_discount BETWEEN 0.05 AND 0.07
                AND l_quantity < 24
        ) TO '{output_path}' (FORMAT PARQUET, COMPRESSION ZSTD);
        """
        start = time.perf_counter()
        self._conn.execute(query)
        elapsed = time.perf_counter() - start

        return {
            "status": "success",
            "profile": "Profile-A (Scan/Agg)",
            "wall_clock_sec": elapsed
        }

    def run_profile_b_multiway_join(self, output_path: str) -> Dict[str, Any]:
        """TPC-H Q5 Local Supplier Volume Query (5-way join)."""
        lineitem_p = os.path.join(self.data_dir, "lineitem.parquet")
        orders_p = os.path.join(self.data_dir, "orders.parquet")
        customer_p = os.path.join(self.data_dir, "customer.parquet")
        supplier_p = os.path.join(self.data_dir, "supplier.parquet")
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        query = f"""
        COPY (
            SELECT
                c.c_nationkey,
                sum(l.l_extendedprice * (1 - l.l_discount)) as revenue
            FROM
                '{customer_p}' c
                JOIN '{orders_p}' o ON c.c_custkey = o.o_custkey
                JOIN '{lineitem_p}' l ON l.l_orderkey = o.o_orderkey
                JOIN '{supplier_p}' s ON l.l_suppkey = s.s_suppkey
            WHERE
                o.o_orderdate >= DATE '1994-01-01'
                AND o.o_orderdate < DATE '1995-01-01'
            GROUP BY
                c.c_nationkey
            ORDER BY
                revenue DESC
        ) TO '{output_path}' (FORMAT PARQUET, COMPRESSION ZSTD);
        """
        start = time.perf_counter()
        self._conn.execute(query)
        elapsed = time.perf_counter() - start

        return {
            "status": "success",
            "profile": "Profile-B (Multi-Join)",
            "wall_clock_sec": elapsed
        }

    def run_profile_c_subquery_window(self, output_path: str) -> Dict[str, Any]:
        """TPC-H Q17 Small-Quantity-Order Revenue Query (Correlated Subquery)."""
        lineitem_p = os.path.join(self.data_dir, "lineitem.parquet")
        part_p = os.path.join(self.data_dir, "part.parquet")
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        query = f"""
        COPY (
            SELECT
                sum(l.l_extendedprice) / 7.0 as avg_yearly
            FROM
                '{lineitem_p}' l
                JOIN '{part_p}' p ON p.p_partkey = l.l_partkey
            WHERE
                l.l_quantity < (
                    SELECT 0.2 * avg(l2.l_quantity)
                    FROM '{lineitem_p}' l2
                    WHERE l2.l_partkey = p.p_partkey
                )
        ) TO '{output_path}' (FORMAT PARQUET, COMPRESSION ZSTD);
        """
        start = time.perf_counter()
        self._conn.execute(query)
        elapsed = time.perf_counter() - start

        return {
            "status": "success",
            "profile": "Profile-C (Subquery/Window)",
            "wall_clock_sec": elapsed
        }

    def close(self):
        self._conn.close()
