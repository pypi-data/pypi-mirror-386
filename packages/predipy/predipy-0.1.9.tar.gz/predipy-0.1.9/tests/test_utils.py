import pytest
import pandas as pd
from predipy.utils.validation import validate_shape
from predipy.utils.io_helpers import load_dataset
from predipy.utils.timing import time_func

class TestValidation:
    def test_validate_shape(self):
        X = pd.DataFrame({'a': [1, 2]})
        y = pd.Series([3, 4])
        validate_shape(X, y)  # No error
        with pytest.raises(ValueError):
            validate_shape(X, pd.Series([3]))  # Mismatch

class TestIOHelpers:
    def test_load_dataset(self, tmp_path):
        # Create dummy CSV
        df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
        path = tmp_path / "test.csv"
        df.to_csv(path, index=False)
        loaded = load_dataset(str(path))
        pd.testing.assert_frame_equal(loaded, df)

class TestTiming:
    def test_time_func(self):
        def slow_func():
            import time
            time.sleep(0.1)
            return 42
        timed_slow = time_func(slow_func)  # Wrapped func
        result, duration = timed_slow()  # Unpack tuple
        assert result == 42
        assert duration > 0.09  # Approx 0.1s
