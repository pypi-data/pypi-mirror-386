from collections.abc import Callable
from typing import override


# This class is used to wrap functions and provide a consistent interface.
class Function:
    """
    Function class used to wrap functions and provide a consistent interface.
    """

    def __init__(self, func: Callable | list[Callable]):
        if isinstance(func, Function):
            # If already a Function, just unwrap it
            self.func = func.func
            self.__name__ = func.__name__
        elif isinstance(func, list):
            assert all(isinstance(f, Callable) for f in func), ("All function(s) must be callable")
            self.func = func
            self.__name__ = ", ".join(
                getattr(f, "__name__", f.__class__.__name__) for f in func
            )
        elif callable(func):
            self.func = func
            self.__name__ = getattr(func, "__name__", func.__class__.__name__)

    def __call__(self, *args, **kwargs):
        if isinstance(self.func, list):
            result = self.func[0](*args, **kwargs)
            for f in self.func[1:]:
                result = f(result)
            return result
        else:
            return self.func(*args, **kwargs)
            
    @override
    def __repr__(self):
        return f"Function[{self.__name__}]"


def func(func):
    # this is to the decorator for the Function class.
    # it's simple i know 🙃
    return Function(func)



