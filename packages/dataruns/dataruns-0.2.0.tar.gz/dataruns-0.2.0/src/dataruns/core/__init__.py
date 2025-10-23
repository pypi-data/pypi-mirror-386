"""
Dataruns Core Module
===================

This module contains the core functionality for pipeline creation and data transformations.

Components:
- pipeline: Pipeline and Make_Pipeline classes for chaining operations
- transforms: Comprehensive set of data transformation classes
- types: Core data types and function wrappers

Example Usage:
    >>> from dataruns.core import Pipeline
    >>> from dataruns.core.transforms import standard_scaler
    
    >>> # Create individual transforms
    >>> scaler = standard_scaler()
    >>> pipeline = Pipeline(scaler)
"""
# Pipeline imports
from .pipeline import Make_Pipeline, Pipeline

# Transform factories
from .transforms import fill_na, select_columns, standard_scaler, get_transforms

# Type imports
from .types import Function, func

# Define what gets exported with "from dataruns.core import *"
__all__ = [
    # Pipeline classes
    'Pipeline',
    'Make_Pipeline',
    
    # Core types
    'Function',
    'func',
    
    # Transforms
    'standard_scaler',
    'fill_na',
    'select_columns',
    'get_transforms'
]
