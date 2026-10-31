import os
import time
import pandas as pd
from typing import Dict, Any

class NaivePandasBaseline:
    """
    Simulates standard code-generation LLM agents (e.g. PandasAI) loading entire DataFrames in memory.
    Eagerly materializes matrices into host RAM, triggering high peak RSS or OOM terminations on large scales.
    """

    def __init__(self, data_dir: str):
        self.data_dir = data_dir

    def run_profile_a_scan_agg(self, output_path: str) -> Dict[str, Any]:
        """TPC-H Q6 Forecasting Revenue Change Query."""
        lineitem_p = os.path.join(self.data_dir, "lineitem.parquet")
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        start = time.perf_counter()
        df = pd.read_parquet(lineitem_p)
        filtered = df[
            (df["l_shipdate"] >= "1994-01-01")
            & (df["l_shipdate"] < "1995-01-01")
            & (df["l_discount"] >= 0.05)
            & (df["l_discount"] <= 0.07)
            & (df["l_quantity"] < 24)
        ]
        revenue = (filtered["l_extendedprice"] * filtered["l_discount"]).sum()
        res = pd.DataFrame([{"revenue": revenue}])
        res.to_parquet(output_path)
        elapsed = time.perf_counter() - start

        return {
            "status": "success",
            "profile": "Profile-A (Scan/Agg)",
            "rows": len(res),
            "wall_clock_sec": elapsed
        }

    def run_profile_b_multiway_join(self, output_path: str) -> Dict[str, Any]:
        """TPC-H Q5 Local Supplier Volume Query (Multi-Way Join in Memory)."""
        lineitem_p = os.path.join(self.data_dir, "lineitem.parquet")
        orders_p = os.path.join(self.data_dir, "orders.parquet")
        customer_p = os.path.join(self.data_dir, "customer.parquet")
        supplier_p = os.path.join(self.data_dir, "supplier.parquet")
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        start = time.perf_counter()
        cust = pd.read_parquet(customer_p)
        orders = pd.read_parquet(orders_p)
        lineitem = pd.read_parquet(lineitem_p)
        supp = pd.read_parquet(supplier_p)

        # In-memory merge cascade
        m1 = pd.merge(cust, orders, left_on="c_custkey", right_on="o_custkey")
        m2 = pd.merge(m1, lineitem, left_on="o_orderkey", right_on="l_orderkey")
        m3 = pd.merge(m2, supp, left_on="l_suppkey", right_on="s_suppkey")

        filtered = m3[(m3["o_orderdate"] >= "1994-01-01") & (m3["o_orderdate"] < "1995-01-01")]
        filtered["revenue"] = filtered["l_extendedprice"] * (1.0 - filtered["l_discount"])
        res = filtered.groupby("c_nationkey")["revenue"].sum().reset_index().sort_values("revenue", ascending=False)
        res.to_parquet(output_path)
        elapsed = time.perf_counter() - start

        return {
            "status": "success",
            "profile": "Profile-B (Multi-Join)",
            "rows": len(res),
            "wall_clock_sec": elapsed
        }

    def run_profile_c_subquery_window(self, output_path: str) -> Dict[str, Any]:
        """TPC-H Q17 Small-Quantity-Order Revenue Query (In-Memory)."""
        lineitem_p = os.path.join(self.data_dir, "lineitem.parquet")
        part_p = os.path.join(self.data_dir, "part.parquet")
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        start = time.perf_counter()
        lineitem = pd.read_parquet(lineitem_p)
        part = pd.read_parquet(part_p)

        # In-memory aggregation & join
        avg_q = lineitem.groupby("l_partkey")["l_quantity"].mean().reset_index()
        avg_q["threshold"] = avg_q["l_quantity"] * 0.2
        avg_q = avg_q.drop(columns=["l_quantity"])

        m1 = pd.merge(lineitem, part, left_on="l_partkey", right_on="p_partkey")
        m2 = pd.merge(m1, avg_q, on="l_partkey")
        filtered = m2[m2["l_quantity"] < m2["threshold"]]
        avg_yearly = filtered["l_extendedprice"].sum() / 7.0
        res = pd.DataFrame([{"avg_yearly": avg_yearly}])
        res.to_parquet(output_path)
        elapsed = time.perf_counter() - start

        return {
            "status": "success",
            "profile": "Profile-C (Subquery/Window)",
            "rows": len(res),
            "wall_clock_sec": elapsed
        }
