"""
Unit tests for Function wrapper class.
"""

import pytest
from dataruns.core.types import Function, func


class TestFunctionWrapper:
    """Test cases for the Function class."""

    def test_function_wraps_callable(self):
        """Test wrapping a simple callable."""
        def add_one(x):
            return x + 1

        wrapper = Function(add_one)
        assert wrapper(5) == 6

    def test_function_preserves_name(self):
        """Test that Function preserves the original function name."""
        def my_func(x):
            return x

        wrapper = Function(my_func)
        assert wrapper.__name__ == 'my_func'

    def test_function_wraps_lambda(self):
        """Test wrapping a lambda function."""
        add_five = lambda x: x + 5
        wrapper = Function(add_five)

        assert wrapper(10) == 15

    def test_function_wraps_list_of_callables(self):
        """Test wrapping a list of callables."""
        def add_one(x):
            return x + 1

        def multiply_two(x):
            return x * 2

        wrapper = Function([add_one, multiply_two])
        # Should apply add_one then multiply_two
        assert wrapper(5) == 12  # (5 + 1) * 2

    def test_function_list_composition_order(self):
        """Test that list functions are composed in order."""
        def add_ten(x):
            return x + 10

        def divide_two(x):
            return x / 2

        wrapper = Function([add_ten, divide_two])
        # (5 + 10) / 2 = 7.5
        assert wrapper(5) == 7.5

    def test_function_wraps_existing_function_wrapper(self):
        """Test wrapping a Function that wraps another Function."""
        def original(x):
            return x * 2

        wrapper1 = Function(original)
        wrapper2 = Function(wrapper1)

        # Should unwrap and use the original function
        assert wrapper2(5) == 10
        assert wrapper2.__name__ == 'original'

    def test_function_list_name_composition(self):
        """Test that list of functions has composite name."""
        def func1(x):
            return x

        def func2(x):
            return x

        wrapper = Function([func1, func2])
        assert 'func1' in wrapper.__name__
        assert 'func2' in wrapper.__name__

    def test_function_with_kwargs(self):
        """Test Function with keyword arguments."""
        def add_value(x, value=10):
            return x + value

        wrapper = Function(add_value)
        assert wrapper(5, value=20) == 25

    def test_function_list_validation_not_callable(self):
        """Test that Function list must contain only callables."""
        with pytest.raises(AssertionError):
            Function([lambda x: x, "not_callable"])

    def test_function_repr(self):
        """Test Function string representation."""
        def my_func(x):
            return x

        wrapper = Function(my_func)
        repr_str = repr(wrapper)

        assert "Function" in repr_str
        assert "my_func" in repr_str

    def test_function_repr_with_lambda(self):
        """Test Function repr with lambda."""
        wrapper = Function(lambda x: x)
        repr_str = repr(wrapper)

        assert "Function" in repr_str
        assert "<lambda>" in repr_str


class TestFuncDecorator:
    """Test cases for the @func decorator."""

    def test_func_decorator_wraps_function(self):
        """Test that @func decorator wraps function."""
        @func
        def my_func(x):
            return x + 1

        assert isinstance(my_func, Function)
        assert my_func(5) == 6

    def test_func_decorator_preserves_name(self):
        """Test that @func decorator preserves function name."""
        @func
        def my_decorated_func(x):
            return x

        assert my_decorated_func.__name__ == 'my_decorated_func'

    def test_func_decorator_with_kwargs(self):
        """Test @func decorator with keyword arguments."""
        @func
        def add_value(x, y=10):
            return x + y

        assert add_value(5) == 15
        assert add_value(5, y=20) == 25

    def test_func_decorator_chaining(self):
        """Test chaining decorated functions."""
        @func
        def add_one(x):
            return x + 1

        @func
        def multiply_two(x):
            return x * 2

        # Manual chaining
        result = multiply_two(add_one(5))
        assert result == 12  # (5 + 1) * 2
