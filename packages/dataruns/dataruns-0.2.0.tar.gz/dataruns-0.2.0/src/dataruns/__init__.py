"""
Dataruns
========

Dataruns is a Python package designed for managing and processing data pipelines.
It provides tools for data transformation, loading, and sourcing, making it easier
to handle complex data workflows.

Main Components:
- core: Pipeline creation and data transformations
- source: Data extraction from various sources (CSV, Excel, SQLite)

Example Usage:
    >>> from dataruns import Pipeline
    >>> from dataruns.core.transforms import standard_scaler
    >>> from dataruns.source import CSVSource
    
    >>> # Extract data
    >>> source = CSVSource('data.csv')
    >>> data = source.extract_data()
    
    >>> # Create pipeline
    >>> scaler = standard_scaler()
    >>> pipeline = Pipeline(scaler)
    >>> result = pipeline(data)

😁😁
"""

# Version information
__version__ = "0.2.0"



# Core imports
import numpy as np

# Expose commonly used external dependencies
import pandas as pd

from .core import Make_Pipeline, Pipeline

# Source imports
from .source import CSVSource, SQLiteSource, XLSsource, load_data

# Make pandas and numpy available at package level for convenience
__all__ = [
    # Version info
    '__version__',
    
    # Core pipeline classes
    'Pipeline',
    'Make_Pipeline',
    
    # Data sources
    'CSVSource',
    'XLSsource',
    'SQLiteSource',
    'load_data',
    
    # External dependencies
    'pd',
    'np'
]

# Package level convenience function
def load_csv(file_path, **kwargs):
    """
    Convenience function to load CSV data.
    
    Args:
        file_path (str): Path to CSV file
        **kwargs: Additional arguments passed to CSVSource
        
    Returns:
        pandas.DataFrame: Loaded data
        
    Example:
        >>> data = load_csv('data.csv')
    """
    source = CSVSource(file_path=file_path, **kwargs)
    return source.extract_data()


# Add convenience functions to __all__
__all__.extend(['load_csv'])


