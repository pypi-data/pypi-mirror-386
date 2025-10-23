# Validasi sederhana
import pandas as pd

def validate_shape(X: pd.DataFrame, y: pd.Series = None) -> None:
    if y is not None and len(X) != len(y):
        raise ValueError(f"Shape mismatch: X len {len(X)}, y len {len(y)}")

