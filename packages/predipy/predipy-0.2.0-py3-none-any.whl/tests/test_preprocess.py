import pytest
import pandas as pd
import numpy as np
from predipy.preprocess.numeric import handle_missing, scale_numeric
from predipy.preprocess.encoder import encode_categorical
from predipy.preprocess.text import clean_text

class TestNumericPreprocess:
    @pytest.fixture
    def numeric_df(self):
        return pd.DataFrame({'col1': [1, np.nan, 3], 'col2': [4, 5, 6]})

    def test_handle_missing(self, numeric_df):
        df_filled = handle_missing(numeric_df)
        assert not df_filled.isnull().any().any()
        assert df_filled['col1'].mean() == pytest.approx((1 + 3) / 2)  # Mean fill

    def test_scale_numeric(self, numeric_df):
        df_scaled = scale_numeric(numeric_df)
        assert df_scaled['col1'].mean() == pytest.approx(0)
        assert df_scaled['col1'].std() == pytest.approx(1)

class TestEncoder:
    def test_encode_categorical(self):
        df = pd.DataFrame({'cat': ['a', 'b', 'a']})
        df_encoded = encode_categorical(df, method='label')
        assert 'cat' in df_encoded.columns
        assert set(df_encoded['cat']) == {0, 1}  # Label encoded

class TestText:
    def test_clean_text(self):
        dirty = "Hello  world! @user #hashtag"
        clean = clean_text(dirty)
        assert clean == "hello world"  # Lower, remove special
