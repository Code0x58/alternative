from inspect import ismethod
from typing import Callable
from unittest.mock import Mock

import pytest

from alternative import implementation_decorator, implementation_method_decorator


def i_only(imp: Callable[[], int],/): return imp

def i_with_kwargs(imp: Callable[[], int], /, **kwargs): return imp

def i_after_arg(self, /, imp, **kwargs): return imp

def i_after_arg_with_kwargs(self, imp=object(), **kwargs): return imp

@pytest.mark.parametrize("f,args,kwargs", [
    (i_only, False, False),
    (i_with_kwargs, False, True),
    (i_after_arg, True, False),
    (i_after_arg_with_kwargs, True, False),
])
def test_pass_through_function(f, args, kwargs):
    """The arguments and kwargs are passed through to the underlying function."""
    f_mock = Mock(side_effect=f)
    if args:
        args = [1]
        wrapper = implementation_method_decorator
    else:
        args= []
        wrapper = implementation_decorator
    f_wrapped = wrapper(f_mock)

    if kwargs:
        kwargs = {"k": "v"}
    else:
        kwargs = {}

    implmentation = object()

    direct = f_wrapped(*args, implmentation, **kwargs)
    assert f_mock.call_count == 1
    intermediate = f_wrapped(*args, **kwargs)
    decorated = intermediate(implmentation)
    assert f_mock.call_count == 2
    # both approaches result in all the same underlying call
    assert direct is implmentation
    assert direct is decorated
    assert f_mock.call_args_list[0] == f_mock.call_args_list[1]

def test_method_descriptor():
    """Decorated methods behave as descriptors."""

    class C:
        @implementation_method_decorator
        def m(self, imp, /, **kwargs):
            return imp

    c = C()
    implementation = object()

    # direct invocation passes through the arguments
    assert c.m(implementation) is implementation

    bound = c.m()
    assert bound(implementation) is implementation
