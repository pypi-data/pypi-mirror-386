"""Testing utilities for introspection and validation.

This module provides utility functions for working with tests, including:
- Asserting that all objects in the source have corresponding test objects
- Generating the content for a conftest.py file

Returns:
    Various utility functions for testing introspection and validation.

"""

from collections.abc import Callable
from types import ModuleType
from typing import Any

from winipedia_utils.modules.function import is_abstractmethod
from winipedia_utils.modules.module import get_objs_from_obj, make_obj_importpath
from winipedia_utils.testing.assertions import assert_with_msg
from winipedia_utils.testing.convention import (
    get_obj_from_test_obj,
    make_test_obj_importpath_from_obj,
    make_untested_summary_error_msg,
)


def assert_no_untested_objs(
    test_obj: ModuleType | type | Callable[..., Any],
) -> None:
    """Assert that all objects in the source have corresponding test objects.

    This function verifies that every object (function, class, or method) in the
    source module or class has a corresponding test object in the test module or class.

    Args:
        test_obj: The test object (module, class, or function) to check

    Raises:
        AssertionError: If any object in the source lacks a corresponding test object,
            with a detailed error message listing the untested objects

    """
    test_objs = get_objs_from_obj(test_obj)
    test_objs_paths = {make_obj_importpath(o) for o in test_objs}

    obj = get_obj_from_test_obj(test_obj)
    objs = get_objs_from_obj(obj)
    supposed_test_objs_paths = {make_test_obj_importpath_from_obj(o) for o in objs}

    untested_objs = supposed_test_objs_paths - test_objs_paths

    assert_with_msg(not untested_objs, make_untested_summary_error_msg(untested_objs))


def assert_isabstrct_method(method: Any) -> None:
    """Assert that a method is an abstract method.

    Args:
        method: The method to check

    Raises:
        AssertionError: If the method is not an abstract method

    """
    assert_with_msg(
        is_abstractmethod(method),
        f"Expected {method} to be abstract method",
    )
