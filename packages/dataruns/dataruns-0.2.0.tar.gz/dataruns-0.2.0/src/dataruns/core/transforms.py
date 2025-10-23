# This script is not a replacement to the transformations implemented in pandas and numpy. It is just an implementation of commonly used transforms for convenience.
from collections.abc import Callable
from typing import Any, cast

import numpy as np
import pandas as pd


def _make_callable(name: str, fn: Callable) -> Callable:
    """A friendly __repr__ attachment to a callable via closure."""

    def wrapped(data):
        return fn(data)

    try:
        wrapped.__name__ = name
    except Exception:
        pass

    def _repr():
        return f"{name}()"

    wrapped.__repr__ = _repr
    return wrapped


def standard_scaler() -> Callable: # Gen by Ai
    """Return a callable that standardizes input arrays or DataFrames.

    State (mean_/std_) is kept in the closure and computed on first call.
    """

    # keep separate stats for DataFrame (pandas.Series) and ndarray (numpy.ndarray)
    mean_pd = None
    std_pd = None
    mean_np = None
    std_np = None

    def _scaler(data: np.ndarray | pd.DataFrame) -> np.ndarray | pd.DataFrame:
        nonlocal mean_pd, std_pd, mean_np, std_np
        if isinstance(data, pd.DataFrame):
            # Use pandas Series for mean/std when working with DataFrame
            if mean_pd is None:
                mean_pd = data.mean()
                std_pd = data.std()
            mean_s = mean_pd
            std_s = std_pd
            # pandas will broadcast Series correctly across DataFrame
            assert std_s is not None
            result = (data - mean_s) / std_s
        else:
            # Ensure numpy arrays for ndarray path
            arr = np.asarray(data)
            if mean_np is None:
                mean_np = np.mean(arr, axis=0)
                std_np = np.std(arr, axis=0)
            mean_a = mean_np
            std_a = std_np
            # avoid division by zero
            assert std_a is not None
            safe_std = np.where(std_a == 0, 1, std_a)
            result = (arr - mean_a) / safe_std
        return result

    return _make_callable("StandardScaler", _scaler)


def fill_na(strategy: str = "mean", value: Any = None) -> Callable: # Gen by Ai
    """Return a callable that fills NaNs according to `strategy`.

    Supported strategies: 'mean', 'median', 'ffill', 'bfill', 'constant'
    """

    fill_values_ = None

    def _fill(data: np.ndarray | pd.DataFrame) -> np.ndarray | pd.DataFrame:
        nonlocal fill_values_
        if isinstance(data, pd.DataFrame):
            result = data.copy()
            if strategy == "mean":
                if fill_values_ is None:
                    fill_values_ = data.mean()
                return cast(pd.DataFrame, result.fillna(fill_values_))
            elif strategy == "median":
                if fill_values_ is None:
                    fill_values_ = data.median()
                return cast(pd.DataFrame, result.fillna(fill_values_))
            elif strategy == "ffill":
                return cast(pd.DataFrame, result.ffill())
            elif strategy == "bfill":
                return cast(pd.DataFrame, result.bfill())
            elif strategy == "constant":
                return cast(pd.DataFrame, result.fillna(value))
            return result
        else:
            result = data.copy()
            mask = np.isnan(result)
            if strategy == "mean":
                if fill_values_ is None:
                    fill_values_ = np.nanmean(data, axis=0)
                result[mask] = np.broadcast_to(fill_values_, result.shape)[mask]
            elif strategy == "constant":
                result[mask] = value
            return result

    return _make_callable(f"FillNA(strategy='{strategy}')", _fill)


def select_columns(columns: list[str]) -> Callable: # Gen by Ai
    """
    Return a callable that selects specified columns from DataFrame or numpy array.

    For numpy arrays, columns can be indices (int) or names (str) which will be
    looked up from the provided `columns` list.
    """

    def _select(data: np.ndarray | pd.DataFrame) -> np.ndarray | pd.DataFrame:
        if isinstance(data, pd.DataFrame):
            return data[columns]
        else:
            # For numpy arrays, assume columns are indices (integers) or names
            idxs = [columns.index(c) if isinstance(c, str) else c for c in columns]
            return data[:, idxs]

    cols_str = ", ".join(columns[:3])
    if len(columns) > 3:
        cols_str += "..."
    return _make_callable(f"SelectColumns(columns=[{cols_str}])", _select)



def get_transforms() -> list[str]:
    """Return a list of available transform functions in this module.
    
    Returns:
        list[str]: A list of transform function names available for use.
        
    Example:
        >>> print(get_transforms())
        ['standard_scaler', 'fill_na', 'select_columns']
    """
    return [
        'standard_scaler',
        'fill_na',
        'select_columns',
    ]