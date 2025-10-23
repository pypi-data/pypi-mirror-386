import time
from functools import wraps

def time_func(func):
    """Decorator: Time func execution, print duration, return (result, duration)."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        print(f"{func.__name__} took {duration:.2f}s")
        return result, duration  # Tambah tuple ini biar unpack bener
    return wrapper

