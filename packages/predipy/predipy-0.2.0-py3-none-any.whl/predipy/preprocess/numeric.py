# Numeric preprocessing manual
import pandas as pd
import numpy as np

def handle_missing(df: pd.DataFrame, strategy: str = 'mean') -> pd.DataFrame:
    df = df.copy()
    numeric_cols = df.select_dtypes(include=['number']).columns
    for col in numeric_cols:
        if strategy == 'mean':
            fill_val = df[col].mean()
        elif strategy == 'median':
            fill_val = df[col].median()
        else:
            fill_val = df[col].mode().iloc[0] if not df[col].mode().empty else 0
        df[col] = df[col].fillna(fill_val)
    return df.dropna()

def scale_numeric(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    numeric_cols = df.select_dtypes(include=['number']).columns
    for col in numeric_cols:
        data = df[col].values
        mean = np.nanmean(data)
        data = np.nan_to_num(data, nan=mean)
        std = np.std(data, ddof=1)
        if std > 0:
            df[col] = (data - mean) / std
        else:
            df[col] = 0.0  # Avoid NaN for constant cols
    return df
