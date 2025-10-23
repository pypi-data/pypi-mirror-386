# Config umum
import os

class Config:
    def __init__(self, go_binary_path: str = None):
        self.go_binary_path = go_binary_path or os.path.join(os.path.dirname(__file__), "../go_backend/main")
        if not os.path.exists(self.go_binary_path):
            raise ValueError(f"Build Go dulu: cd go_backend && go build -o main main.go\nPath: {self.go_binary_path}")

    def validate(self) -> bool:
        return os.path.exists(self.go_binary_path)
