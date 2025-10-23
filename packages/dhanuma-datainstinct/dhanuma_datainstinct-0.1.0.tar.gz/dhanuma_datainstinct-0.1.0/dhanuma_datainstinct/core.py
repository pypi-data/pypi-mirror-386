import pandas as pd
from .stats import summarize

def profile(file_path: str, max_rows: int = 100000):
    """
    Profile a CSV, JSON, or Excel file and print summary statistics.

    Args:
        file_path (str): Path to the file (.csv, .json, .xlsx).
        max_rows (int): Max number of rows to read for large files.

    Returns:
        dict: Summary of the dataset.
    """
    if file_path.endswith(".csv"):
        df = pd.read_csv(file_path, nrows=max_rows)
    elif file_path.endswith(".json"):
        try:
            df = pd.read_json(file_path)
        except ValueError:
            # Fallback for JSON lines
            df = pd.read_json(file_path, lines=True, nrows=max_rows)
        # df = pd.read_json(file_path, nrows=max_rows)
    elif file_path.endswith(".xlsx"):
        df = pd.read_excel(file_path, nrows=max_rows)
    else:
        raise ValueError("Supported formats: .csv, .json, .xlsx")

    summary = summarize(df)
    print(f"\n Data Profile: {file_path}")
    print("=" * 60)
    print(f"Rows: {len(df)}, Columns: {len(df.columns)}\n")
    
    for col, stats in summary.items():
        print(f" {col}:")
        for key, val in stats.items():
            print(f"  {key}: {val}")
        print("-" * 40)

    return summary

# print("Data profile start")
# print(profile("dhanuma_datainstinct/sample_nested_data.json"))