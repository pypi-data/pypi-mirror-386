"""Test the 'builtins' module."""

import sys
import warnings

import pytest


def test_import_warnings():
    """Checking the warning is printed for all versions that don't backport the classes."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        from py_back import builtins  # noqa: F401

        if sys.version_info >= (3, 9):
            match_text = "Consider 'from builtins import ...' instead of 'from py_back.builtins import ...'"
            assert len(w) == 1, "Expected a warning but none was raised"
            assert issubclass(w[-1].category, UserWarning)
            assert match_text in str(w[-1].message)
        else:
            assert len(w) == 0


@pytest.mark.skipif(sys.version_info >= (3, 9), reason="Features included at python 3.9")
def test_backported_str():
    """Here are tested all methods backported for the 'str' class."""
    from py_back.builtins import str

    old_str = "Hello world!"

    for backported_method in ("removeprefix", "removesuffix"):
        assert hasattr(old_str, backported_method) is False

    assert str("TestHook").removeprefix("Test") == "Hook"
    assert str("BaseTestCase").removeprefix("Test") == "BaseTestCase"

    assert str("MiscTests").removesuffix("Tests") == "Misc"
    assert str("TmpDirMixin").removesuffix("Tests") == "TmpDirMixin"


@pytest.mark.skipif(sys.version_info >= (3, 9), reason="Features included at python 3.9")
def test_backported_dict():
    """Here are tested all methods backported for the 'str' class."""
    from py_back.builtins import dict

    my_dict = dict({"a": 1, "b": 2})
    result = my_dict | {"c": 3}
    assert my_dict == {"a": 1, "b": 2}
    assert result == {"a": 1, "b": 2, "c": 3}
