from collections.abc import Callable
from itertools import chain
from typing import override

import numpy as np
import pandas as pd

from dataruns.core.types import Function

# Funtion class has been moved to types.py

# This file contains the core pipeline class and the pipeline builder class
class Pipeline:
    """
    Unified interface for chaining different Ops for data.
    """

    def __init__(self, *functions: Function | Callable, verbose: bool = False):
        if len(functions) == 0:
            raise ValueError("No functions provided at all")
        self.verbose = verbose
        # Convert all functions to Function instances
        self.functions = [
            f if isinstance(f, Function) else Function(f) for f in functions
        ]

    def __call__(self, data: np.ndarray | pd.DataFrame):
        _data = self._func_check(data)
        return self._run(_data)

    def _func_check(self, data):
        if isinstance(data, dict):
            raise TypeError(
                "Data cannot be a dictionary.Convert to pandas dataframe first"
            )
        if isinstance(data, list):
            return np.array(data)
        return data

    def _run(self, data: np.ndarray | pd.DataFrame):
        result = data  # we dont want the orig data to be processed after each iter 🙃 though not conventional but it works
        for i, function in enumerate(self.functions):
            try:
                result = function(result)
                if result is None:
                    raise ValueError(f"Function {function} returned None")
                if self.verbose:
                    print(f"Applying function {i + 1}/{len(self.functions)}: {function}, Output: \n{result}\n")
            except ValueError:
                # Re-raise ValueError as-is (our None check)
                raise
            except Exception as e:
                raise RuntimeError(
                    f"Error in pipeline at function {i + 1}: {function}"
                ) from e
        return result

    @override
    def __repr__(self):
        format_string = f"{self.__class__.__name__}("
        for function in self.functions:
            format_string += f"\n    {function}"
        format_string += "\n)"
        return format_string


class Make_Pipeline:
    """
    Used For building Pipelines.
    """

    def __init__(self):
        self.functions = []

    def add(self, *function):
        """
        Add a function to the pipeline
        """
        if len(function) == 1:
            function = function[0]
        elif len(function) > 1:
            function = list(function)
        elif len(function) == 0:
            raise ValueError("No function provided at all")

        self.functions.append(function)

    def build(self) -> Pipeline:
        """
        Build and return the pipeline with added functions
        """
        # Flatten the list of functions if any were added as lists
        flattened_functions = list(
            chain.from_iterable(
                func if isinstance(func, list) else [func] for func in self.functions
            )
        )

        # Create and return new pipeline with flattened functions
        return Pipeline(*flattened_functions)

    @override
    def __repr__(self):
        return f"PipelineBuilder({self.functions})"
