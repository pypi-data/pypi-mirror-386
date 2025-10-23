"""
Unit tests for the Pipeline and Make_Pipeline classes.
"""

import numpy as np
import pandas as pd
import pytest

from dataruns.core import Make_Pipeline, Pipeline
from dataruns.core.types import Function


class TestPipeline:
    """Test cases for the Pipeline class."""

    def test_pipeline_initialization_with_single_function(self):
        """Test Pipeline initialization with a single function."""
        def dummy_func(x):
            return x * 2

        pipeline = Pipeline(dummy_func)
        assert len(pipeline.functions) == 1
        assert isinstance(pipeline.functions[0], Function)

    def test_pipeline_initialization_with_multiple_functions(self):
        """Test Pipeline initialization with multiple functions."""
        def func1(x):
            return x * 2

        def func2(x):
            return x + 1

        pipeline = Pipeline(func1, func2)
        assert len(pipeline.functions) == 2

    def test_pipeline_initialization_empty_raises_error(self):
        """Test that Pipeline raises error when no functions provided."""
        with pytest.raises(ValueError, match="No functions provided"):
            Pipeline()

    def test_pipeline_execution_with_numpy_array(self):
        """Test Pipeline execution with NumPy array."""
        def add_one(x):
            return x + 1

        def multiply_two(x):
            return x * 2

        data = np.array([1, 2, 3])
        pipeline = Pipeline(add_one, multiply_two)
        result = pipeline(data)

        expected = np.array([4, 6, 8])
        assert np.allclose(result, expected)

    def test_pipeline_execution_with_dataframe(self):
        """Test Pipeline execution with pandas DataFrame."""
        def add_one(x):
            return x + 1

        df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        pipeline = Pipeline(add_one)
        result = pipeline(df)

        expected = pd.DataFrame({'a': [2, 3, 4], 'b': [5, 6, 7]})
        assert result.equals(expected)

    def test_pipeline_converts_list_to_array(self):
        """Test that Pipeline converts list input to array."""
        def identity(x):
            return x

        data = [1, 2, 3]
        pipeline = Pipeline(identity)
        result = pipeline(data)

        assert isinstance(result, np.ndarray)
        assert np.array_equal(result, np.array([1, 2, 3]))

    def test_pipeline_rejects_dict_input(self):
        """Test that Pipeline rejects dictionary input."""
        def identity(x):
            return x

        pipeline = Pipeline(identity)
        with pytest.raises(TypeError, match="Data cannot be a dictionary"):
            pipeline({'a': 1, 'b': 2})

    def test_pipeline_function_returning_none_raises_error(self):
        """Test that Pipeline raises error if function returns None."""
        def returns_none(x):
            return None

        data = np.array([1, 2, 3])
        pipeline = Pipeline(returns_none)

        with pytest.raises(ValueError, match="returned None"):
            pipeline(data)

    def test_pipeline_exception_handling(self):
        """Test Pipeline exception handling and error reporting."""
        def bad_func(x):
            raise ValueError("Test error")

        data = np.array([1, 2, 3])
        pipeline = Pipeline(bad_func)

        with pytest.raises(RuntimeError, match="Error in pipeline"):
            pipeline(data)

    def test_pipeline_verbose_mode(self, capsys):
        """Test Pipeline verbose mode output."""
        def add_one(x):
            return x + 1

        def multiply_two(x):
            return x * 2

        data = np.array([1, 2])
        pipeline = Pipeline(add_one, multiply_two, verbose=True)
        pipeline(data)

        captured = capsys.readouterr()
        assert "Applying function" in captured.out
        assert "1/2" in captured.out
        assert "2/2" in captured.out

    def test_pipeline_repr(self):
        """Test Pipeline string representation."""
        def add_one(x):
            return x + 1

        pipeline = Pipeline(add_one)
        repr_str = repr(pipeline)

        assert "Pipeline" in repr_str
        assert "add_one" in repr_str


class TestMakePipeline:
    """Test cases for the Make_Pipeline builder class."""

    def test_make_pipeline_initialization(self):
        """Test Make_Pipeline initialization."""
        builder = Make_Pipeline()
        assert builder.functions == []

    def test_make_pipeline_add_single_function(self):
        """Test adding a single function."""
        def func(x):
            return x

        builder = Make_Pipeline()
        builder.add(func)

        assert len(builder.functions) == 1

    def test_make_pipeline_add_multiple_functions(self):
        """Test adding multiple functions at once."""
        def func1(x):
            return x

        def func2(x):
            return x

        def func3(x):
            return x

        builder = Make_Pipeline()
        builder.add(func1, func2, func3)

        assert len(builder.functions) == 3

    def test_make_pipeline_add_list_of_functions(self):
        """Test adding a list of functions."""
        def func1(x):
            return x

        def func2(x):
            return x

        builder = Make_Pipeline()
        builder.add([func1, func2])

        assert len(builder.functions) == 1
        assert isinstance(builder.functions[0], list)

    def test_make_pipeline_add_empty_raises_error(self):
        """Test that adding no functions raises error."""
        builder = Make_Pipeline()
        with pytest.raises(ValueError, match="No function provided"):
            builder.add()

    def test_make_pipeline_build_creates_pipeline(self):
        """Test that build() creates a Pipeline."""
        def func1(x):
            return x + 1

        builder = Make_Pipeline()
        builder.add(func1)
        pipeline = builder.build()

        assert isinstance(pipeline, Pipeline)

    def test_make_pipeline_build_flattens_functions(self):
        """Test that build() flattens nested function lists."""
        def func1(x):
            return x

        def func2(x):
            return x

        def func3(x):
            return x

        builder = Make_Pipeline()
        builder.add([func1, func2])
        builder.add(func3)
        pipeline = builder.build()

        # Should have 3 functions after flattening
        assert len(pipeline.functions) == 3

    def test_make_pipeline_build_execution(self):
        """Test that built pipeline executes correctly."""
        def add_one(x):
            return x + 1

        def multiply_two(x):
            return x * 2

        builder = Make_Pipeline()
        builder.add(add_one, multiply_two)
        pipeline = builder.build()

        data = np.array([1, 2, 3])
        result = pipeline(data)

        expected = np.array([4, 6, 8])
        assert np.allclose(result, expected)

    def test_make_pipeline_repr(self):
        """Test Make_Pipeline string representation."""
        def func(x):
            return x

        builder = Make_Pipeline()
        builder.add(func)
        repr_str = repr(builder)

        assert "PipelineBuilder" in repr_str
