from datainstinct import profile
import tempfile
import pandas as pd
import os

def test_profile_csv():
    df = pd.DataFrame({
        "name": ["A", "B", "C"],
        "age": [25, 30, 35]
    })
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    df.to_csv(temp.name, index=False)

    summary = profile(temp.name)
    assert "name" in summary
    assert "age" in summary
    os.remove(temp.name)
