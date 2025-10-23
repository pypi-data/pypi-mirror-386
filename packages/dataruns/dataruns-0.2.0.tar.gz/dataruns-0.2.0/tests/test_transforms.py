"""
Unit tests for transform functions.
"""

import pytest
import numpy as np
import pandas as pd
from dataruns.core.transforms import standard_scaler, fill_na, select_columns


class TestStandardScaler:
    """Test cases for standard_scaler transform."""

    def test_standard_scaler_with_numpy_array(self):
        """Test standard_scaler with NumPy array."""
        scaler = standard_scaler()
        data = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])

        result = scaler(data)

        # Check mean is approximately 0 and std is approximately 1
        assert np.allclose(np.mean(result, axis=0), 0, atol=1e-10)
        assert np.allclose(np.std(result, axis=0), 1)

    def test_standard_scaler_with_dataframe(self):
        """Test standard_scaler with pandas DataFrame."""
        scaler = standard_scaler()
        df = pd.DataFrame({'a': [1.0, 3.0, 5.0], 'b': [2.0, 4.0, 6.0]})

        result = scaler(df)

        # Check mean is approximately 0 for each column
        assert np.allclose(result.mean(), 0, atol=1e-10)
        # Check std is approximately 1 for each column
        assert np.allclose(result.std(), 1)

    def test_standard_scaler_with_zero_std(self):
        """Test standard_scaler with constant column (zero std)."""
        scaler = standard_scaler()
        data = np.array([[1.0, 5.0], [1.0, 5.0], [1.0, 5.0]])

        result = scaler(data)

        # First column should be 0 (no std, so div by 1)
        assert np.allclose(result[:, 0], 0)

    def test_standard_scaler_stateful_behavior(self):
        """Test that standard_scaler remembers state between calls."""
        scaler = standard_scaler()

        # First call
        data1 = np.array([[1.0, 2.0], [3.0, 4.0]])
        result1 = scaler(data1)

        # Second call with different data
        data2 = np.array([[10.0, 20.0], [30.0, 40.0]])
        result2 = scaler(data2)

        # result2 should use data1's mean and std, not data2's
        # So values should be much larger
        assert np.max(np.abs(result2)) > np.max(np.abs(result1))

    def test_standard_scaler_callable_representation(self):
        """Test string representation of scaler."""
        scaler = standard_scaler()
        assert "StandardScaler" in repr(scaler)


class TestFillNA:
    """Test cases for fill_na transform."""

    def test_fill_na_mean_strategy_with_array(self):
        """Test fill_na with mean strategy on NumPy array."""
        filler = fill_na(strategy='mean')
        data = np.array([[1.0, np.nan], [2.0, 4.0], [3.0, 6.0]])

        result = filler(data)

        # Second column mean is (nan + 4 + 6) / 2 = 5
        assert np.allclose(result[:, 1], [5.0, 4.0, 6.0])

    def test_fill_na_mean_strategy_with_dataframe(self):
        """Test fill_na with mean strategy on pandas DataFrame."""
        filler = fill_na(strategy='mean')
        df = pd.DataFrame({'a': [1, 2, np.nan], 'b': [np.nan, 4, 6]})

        result = filler(df)

        # Check no NaNs remain
        assert not result.isna().any().any()

    def test_fill_na_median_strategy(self):
        """Test fill_na with median strategy."""
        filler = fill_na(strategy='median')
        df = pd.DataFrame({'a': [1, 2, 3, np.nan]})

        result = filler(df)

        # Median of [1, 2, 3] is 2
        assert not result.isna().any().any()

    def test_fill_na_ffill_strategy(self):
        """Test fill_na with forward fill strategy."""
        filler = fill_na(strategy='ffill')
        df = pd.DataFrame({'a': [1, np.nan, np.nan, 4]})

        result = filler(df)

        # Forward fill: [1, 1, 1, 4]
        expected = [1.0, 1.0, 1.0, 4.0]
        assert result['a'].tolist() == expected

    def test_fill_na_bfill_strategy(self):
        """Test fill_na with backward fill strategy."""
        filler = fill_na(strategy='bfill')
        df = pd.DataFrame({'a': [1, np.nan, np.nan, 4]})

        result = filler(df)

        # Backward fill: [1, 4, 4, 4]
        expected = [1.0, 4.0, 4.0, 4.0]
        assert result['a'].tolist() == expected

    def test_fill_na_constant_strategy(self):
        """Test fill_na with constant value strategy."""
        filler = fill_na(strategy='constant', value=0)
        df = pd.DataFrame({'a': [1, np.nan, 3], 'b': [np.nan, 5, 6]})

        result = filler(df)

        # All NaNs replaced with 0
        assert result.loc[1, 'a'] == 0
        assert result.loc[0, 'b'] == 0

    def test_fill_na_constant_strategy_with_array(self):
        """Test fill_na with constant strategy on NumPy array."""
        filler = fill_na(strategy='constant', value=99)
        data = np.array([[1.0, np.nan], [np.nan, 4.0]])

        result = filler(data)

        assert result[0, 1] == 99
        assert result[1, 0] == 99

    def test_fill_na_stateful_mean(self):
        """Test that fill_na remembers mean from first call."""
        filler = fill_na(strategy='mean')

        # First call
        data1 = np.array([[1.0, 10.0], [3.0, 20.0]])
        result1 = filler(data1)

        # Second call (no NaNs)
        data2 = np.array([[5.0, 100.0], [7.0, 200.0]])
        result2 = filler(data2)

        # Results should be unchanged (no NaNs to fill)
        assert np.array_equal(result2, data2)


class TestSelectColumns:
    """Test cases for select_columns transform."""

    def test_select_columns_with_dataframe_by_name(self):
        """Test select_columns with DataFrame column names."""
        selector = select_columns(['a', 'c'])
        df = pd.DataFrame({'a': [1, 2], 'b': [3, 4], 'c': [5, 6]})

        result = selector(df)

        assert list(result.columns) == ['a', 'c']
        assert result.shape == (2, 2)

    def test_select_columns_with_dataframe_single_column(self):
        """Test select_columns with single column name."""
        selector = select_columns(['a'])
        df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})

        result = selector(df)

        assert list(result.columns) == ['a']

    def test_select_columns_with_array_by_index(self):
        """Test select_columns with NumPy array indices."""
        selector = select_columns([0, 2])
        data = np.array([[1, 2, 3, 4], [5, 6, 7, 8]])

        result = selector(data)

        expected = np.array([[1, 3], [5, 7]])
        assert np.array_equal(result, expected)

    def test_select_columns_with_array_single_index(self):
        """Test select_columns with single index."""
        selector = select_columns([1])
        data = np.array([[1, 2, 3], [4, 5, 6]])

        result = selector(data)

        expected = np.array([[2], [5]])
        assert np.array_equal(result, expected)

    def test_select_columns_invalid_column_name(self):
        """Test select_columns with invalid column name."""
        selector = select_columns(['nonexistent'])
        df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})

        with pytest.raises(KeyError):
            selector(df)

    def test_select_columns_invalid_index(self):
        """Test select_columns with invalid index."""
        selector = select_columns([10])
        data = np.array([[1, 2, 3]])

        with pytest.raises(IndexError):
            selector(data)

    def test_select_columns_empty_selection(self):
        """Test select_columns with empty list."""
        selector = select_columns([])
        df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})

        result = selector(df)

        # Empty DataFrame with correct index
        assert result.shape[0] == 2
        assert result.shape[1] == 0
