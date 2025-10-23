import pandas as pd

def summarize(df: pd.DataFrame):
    summary = {}
    for col in df.columns:
        data = df[col]

        # 🩹 Fix: Convert unhashable data (dicts/lists) to string
        if data.apply(lambda x: isinstance(x, (dict, list))).any():
            print(f"Column '{col}' contains nested data - converting to string for safe profiling.")
            data = data.astype(str)

        dtype = str(data.dtype)
        non_null = data.dropna()

        col_summary = {
            "dtype": dtype,
            "non_null_count": non_null.count(),
            "null_count": data.isnull().sum(),
        }

        # Unique count (safe)
        try:
            col_summary["unique_count"] = non_null.nunique()
        except TypeError:
            col_summary["unique_count"] = "N/A (unhashable)"

        # Numeric columns
        if pd.api.types.is_numeric_dtype(data):
            col_summary.update({
                "mean": round(non_null.mean(), 2),
                "min": round(non_null.min(), 2),
                "max": round(non_null.max(), 2),
                "std": round(non_null.std(), 2)
            })
        # String or object columns
        elif pd.api.types.is_string_dtype(data):
            top = non_null.value_counts().head(1)
            col_summary["top_value"] = top.index[0] if not top.empty else None

        summary[col] = col_summary

    return summary
