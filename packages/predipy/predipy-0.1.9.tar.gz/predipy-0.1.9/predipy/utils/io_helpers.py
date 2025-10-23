7# I/O helpers
import pandas as pd

def load_dataset(file_path: str) -> pd.DataFrame:
    return pd.read_csv(file_path)  # Asumsi CSV, expand nanti
