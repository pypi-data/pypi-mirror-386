# High-level Python API: Wrapper untuk Go backend
import subprocess
import json
import pandas as pd
import numpy as np
import os
from typing import List, Dict, Any
from .config import Config
from .preprocess.text import clean_text  # Tambah import text kalau butuh
from .utils.io_helpers import load_dataset

# Helper preprocess (di sini biar sederhana, bisa dipindah nanti)
def preprocess_data(X: pd.DataFrame, y: pd.Series = None, model_type: str = "regression") -> tuple:
    """Preprocessing sederhana: Handle missing, scale, encode."""
    from .preprocess.numeric import handle_missing, scale_numeric
    from .preprocess.encoder import encode_categorical

    # Handle missing
    X = handle_missing(X)
    if y is not None:
        y = pd.Series(y.fillna(y.mean() if model_type == "regression" else y.mode()[0]))

    # Encode categorical
    X = encode_categorical(X, method='label')

    # Scale numeric
    X = scale_numeric(X)

    # Validasi
    from .utils.validation import validate_shape
    validate_shape(X, y)

    return X, y

class PredipyBase:
    def __init__(self, model_type: str, config: Config = None):
        self.model_type = model_type
        self.config = config or Config()
        self._go_binary = self.config.go_binary_path
        self.model = None

    def _call_go(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Panggil Go backend via JSON arg (fix: pass data as CLI arg, bukan stdin)."""
        # Pastikan path binary ada
        if not os.path.exists(self._go_binary):
            raise FileNotFoundError(f"Go binary not found at: {self._go_binary}")

        # JSON cuma data, action udah di arg
        json_data = json.dumps(data)
        cmd = [self._go_binary, action, json_data]  # [main, "train_regression", '{"X":..., "y":...}']

        print(f"[DEBUG] Command: {' '.join(cmd)}")  # Liat exact call (hapus nanti kalau udah jalan)
        print(f"[DEBUG] JSON payload length: {len(json_data)} chars")  # Konfirm non-empty

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,  # Biar stdout/str, bukan bytes
                check=True,
                timeout=30  # Hindari hang
            )
            print(f"[DEBUG] Go stdout: {repr(result.stdout[:100])}...")  # Potong biar gak spam (hapus nanti)
            print(f"[DEBUG] Go stderr: {result.stderr}")  # Debug stderr (hapus nanti)

            if not result.stdout.strip():
                raise ValueError("Go output empty—check main.go logic for this action")

            # Strip prefix log dari Go (kalau ada echo CLI seperti "Predipy CLI: ...")
            stdout_clean = result.stdout.strip()
            if stdout_clean.startswith("Predipy CLI:"):
                # Ambil setelah prefix (split \n pertama, atau kosong kalau gak ada)
                parts = stdout_clean.split('\n', 1)
                stdout_clean = parts[1].strip() if len(parts) > 1 else ""
                print(f"[DEBUG] Clean stdout after strip: {repr(stdout_clean[:100])}...")

            if not stdout_clean:
                raise ValueError("Go only logged input (no JSON response)—check switch logic in main.go for action '{}'".format(action))

            return json.loads(stdout_clean)
        except subprocess.CalledProcessError as e:
            print(f"[DEBUG] Go exit code: {e.returncode}")
            raise RuntimeError(f"Go backend error (code {e.returncode}): {e.stderr}")
        except json.JSONDecodeError as e:
            print(f"[DEBUG] Invalid JSON from Go: {repr(result.stdout[:200])}")
            raise

class PredipyRegressor(PredipyBase):
    def __init__(self, config: Config = None):
        super().__init__("regression", config)

    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        processed_X, processed_y = preprocess_data(X, y, self.model_type)
        data = {
            "X": processed_X.values.tolist(),
            "y": processed_y.tolist()
        }
        self.model = self._call_go("train_regression", data)["model"]
        print("Model regresi trained!")

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        processed_X, _ = preprocess_data(X, None, self.model_type)
        data = {"X": processed_X.values.tolist(), "model": self.model}
        preds = self._call_go("predict_regression", data)["predictions"]
        return np.array(preds)

class PredipyClassifier(PredipyBase):
    def __init__(self, n_neighbors: int = 3, config: Config = None):
        super().__init__("classification", config)
        self.n_neighbors = n_neighbors

    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        processed_X, processed_y = preprocess_data(X, y, self.model_type)
        data = {
            "X": processed_X.values.tolist(),
            "y": processed_y.tolist(),
            "n_neighbors": self.n_neighbors
        }
        self.model = self._call_go("train_classification", data)["model"]
        print("Model klasifikasi trained!")

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        processed_X, _ = preprocess_data(X, None, self.model_type)
        data = {"X": processed_X.values.tolist(), "model": self.model}
        preds = self._call_go("predict_classification", data)["predictions"]
        return np.array(preds)
