import os
import time
from typing import Dict, Any

try:
    import polars as pl
except ImportError:
    pl = None

class PolarsStreamingBaseline:
    """
    Polars LazyFrame streaming baseline executing out-of-core transformations.
    Uses polars streaming engine (.collect(streaming=True)) for out-of-core evaluation.
    """

    def __init__(self, data_dir: str):
        self.data_dir = data_dir

    def run_profile_a_scan_agg(self, output_path: str) -> Dict[str, Any]:
        """TPC-H Q6 Forecasting Revenue Change Query (Scan & Aggregation Heavy)."""
        lineitem_path = os.path.join(self.data_dir, "lineitem.parquet")
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        start = time.perf_counter()
        q = (
            pl.scan_parquet(lineitem_path)
            .filter(
                (pl.col("l_shipdate") >= pl.lit("1994-01-01"))
                & (pl.col("l_shipdate") < pl.lit("1995-01-01"))
                & (pl.col("l_discount").is_between(0.05, 0.07))
                & (pl.col("l_quantity") < 24)
            )
            .select(
                (pl.col("l_extendedprice") * pl.col("l_discount")).sum().alias("revenue")
            )
        )
        res = q.collect(streaming=True)
        res.write_parquet(output_path)
        elapsed = time.perf_counter() - start

        return {
            "status": "success",
            "profile": "Profile-A (Scan/Agg)",
            "rows": len(res),
            "wall_clock_sec": elapsed
        }

    def run_profile_b_multiway_join(self, output_path: str) -> Dict[str, Any]:
        """TPC-H Q5 Local Supplier Volume Query (Multi-Way Join across 5 tables)."""
        lineitem_p = os.path.join(self.data_dir, "lineitem.parquet")
        orders_p = os.path.join(self.data_dir, "orders.parquet")
        customer_p = os.path.join(self.data_dir, "customer.parquet")
        supplier_p = os.path.join(self.data_dir, "supplier.parquet")
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        start = time.perf_counter()
        li = pl.scan_parquet(lineitem_p)
        ord_ = pl.scan_parquet(orders_p)
        cust = pl.scan_parquet(customer_p)
        supp = pl.scan_parquet(supplier_p)

        # Multi-table relational join
        joined = (
            cust.join(ord_, left_on="c_custkey", right_on="o_custkey")
            .join(li, left_on="o_orderkey", right_on="l_orderkey")
            .join(supp, left_on="l_suppkey", right_on="s_suppkey")
            .filter(
                (pl.col("o_orderdate") >= pl.lit("1994-01-01"))
                & (pl.col("o_orderdate") < pl.lit("1995-01-01"))
            )
            .group_by("c_nationkey")
            .agg(
                (pl.col("l_extendedprice") * (1.0 - pl.col("l_discount"))).sum().alias("revenue")
            )
            .sort("revenue", descending=True)
        )
        res = joined.collect(streaming=True)
        res.write_parquet(output_path)
        elapsed = time.perf_counter() - start

        return {
            "status": "success",
            "profile": "Profile-B (Multi-Join)",
            "rows": len(res),
            "wall_clock_sec": elapsed
        }

    def run_profile_c_subquery_window(self, output_path: str) -> Dict[str, Any]:
        """TPC-H Q17 Small-Quantity-Order Revenue Query (Correlated Subquery / Window Aggregation)."""
        lineitem_p = os.path.join(self.data_dir, "lineitem.parquet")
        part_p = os.path.join(self.data_dir, "part.parquet")
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        start = time.perf_counter()
        li = pl.scan_parquet(lineitem_p)
        pt = pl.scan_parquet(part_p)

        # Subquery: avg quantity per part
        avg_qty = (
            li.group_by("l_partkey")
            .agg((pl.col("l_quantity").mean() * 0.2).alias("threshold_qty"))
        )

        res = (
            li.join(pt, left_on="l_partkey", right_on="p_partkey")
            .join(avg_qty, on="l_partkey")
            .filter(pl.col("l_quantity") < pl.col("threshold_qty"))
            .select(
                (pl.col("l_extendedprice").sum() / 7.0).alias("avg_yearly")
            )
            .collect(streaming=True)
        )
        res.write_parquet(output_path)
        elapsed = time.perf_counter() - start

        return {
            "status": "success",
            "profile": "Profile-C (Subquery/Window)",
            "rows": len(res),
            "wall_clock_sec": elapsed
        }
