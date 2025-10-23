import pandas as pd
from typing import Optional

def encode_categorical(df: pd.DataFrame, method: str = 'label') -> pd.DataFrame:
    """Encode categorical cols to numeric."""
    df = df.copy()
    cat_cols = df.select_dtypes(include=['object', 'category']).columns
    for col in cat_cols:
        if method == 'label':
            # Label encode: unique values to 0,1,2...
            unique_vals = df[col].unique()
            label_map = {val: idx for idx, val in enumerate(unique_vals)}
            df[col] = df[col].map(label_map)
        elif method == 'onehot':
            # One-hot, tapi skip dulu kalau gak dipake
            df = pd.get_dummies(df, columns=[col], prefix=col)
        else:
            raise ValueError(f"Unknown method: {method}")
    return df
