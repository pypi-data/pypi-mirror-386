import pytest
import pandas as pd
import numpy as np
from predipy import PredipyRegressor, PredipyClassifier
from predipy.preprocess.text import clean_text  # Import kalau butuh

@pytest.fixture
def regression_data():
    X = pd.DataFrame({'feature1': [1, 2, 3], 'feature2': [1, 1, 1]})
    y = pd.Series([2, 4, 6])
    return X, y

@pytest.fixture
def classification_data():
    X = pd.DataFrame({'feature1': [1, 2, 3, 4], 'feature2': [1, 2, 1, 2]})
    y = pd.Series([0, 1, 0, 1])
    return X, y

class TestPredipyRegressor:
    def test_fit_predict_regression(self, regression_data):
        X, y = regression_data
        model = PredipyRegressor()
        model.fit(X, y)
        preds = model.predict(X)
        # Assert shape & close to y (toleransi floating point)
        np.testing.assert_array_almost_equal(preds, y.values, decimal=1)
        assert len(preds) == len(y)

class TestPredipyClassifier:
    def test_fit_predict_classification(self, classification_data):
        X, y = classification_data
        model = PredipyClassifier(n_neighbors=2)
        model.fit(X, y)
        preds = model.predict(X)
        # Assert shape & binary classes
        assert len(preds) == len(y)
        assert set(preds).issubset({0, 1})

def test_preprocess_data_integration():
    from predipy.predipy import preprocess_data
    X = pd.DataFrame({'num': [1, np.nan, 3], 'cat': ['a', 'b', 'a']})
    y = pd.Series([1, 2, 3])
    X_proc, y_proc = preprocess_data(X, y, "regression")
    assert not X_proc.isnull().any().any()  # No missing
    assert len(X_proc.columns) == 2  # Encoded cat
