import os
import pandas as pd
from typing import Dict, Any

class NaivePandasBaseline:
    """Simulates standard code-generation LLM agents loading entire dataframes in memory."""

    def run_aggregation_task(self, input_parquet: str, output_parquet: str) -> Dict[str, Any]:
        os.makedirs(os.path.dirname(os.path.abspath(output_parquet)), exist_ok=True)
        df = pd.read_parquet(input_parquet)
        result = df.groupby("l_returnflag").agg({"l_extendedprice": "sum", "l_discount": "mean"}).reset_index()
        result.to_parquet(output_parquet)
        return {"status": "success", "rows": len(result)}
