"""Test the 'enums' module."""

import sys
import warnings

import pytest


def test_import_warnings():
    """Checking the warning is printed for all versions that don't backport the classes."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        from py_back import enum  # noqa: F401

        if sys.version_info >= (3, 11):
            match_text = "Consider 'from enum import ...' instead of 'from py_back.enum import ...'"
            assert len(w) == 1, "Expected a warning but none was raised"
            assert issubclass(w[-1].category, UserWarning)
            assert match_text in str(w[-1].message)
        else:
            assert len(w) == 0


@pytest.mark.skipif(sys.version_info >= (3, 11), reason="ReprEnum is available from python 3.11")
def test_repr_enum():
    """Tests for enum representations.

    Testing behaviors in existing enums that were modified in newer python releases,
    due to the creation of ReprEnum. The used classes are obtained from the
    documentation examples.
    """
    from py_back.enum import IntEnum, IntFlag, auto

    class Color(IntFlag):
        RED = auto()
        GREEN = auto()

    assert Color.RED & 2 is Color(0)
    assert repr(Color.RED | 2) in {"<Color.RED|GREEN: 3>", "<Color.GREEN|RED: 3>"}
    assert str(Color.RED) == "1"

    class Number(IntEnum):
        ONE = 1
        TWO = auto()
        THREE = 3

    assert Number.TWO == 2
    assert Number.ONE + Number.THREE == 4
    assert repr(Number.ONE) == "<Number.ONE: 1>"
    assert str(Number.TWO) == "2"


@pytest.mark.skipif(sys.version_info >= (3, 11), reason="StrEnum is available from python 3.11")
def test_str_enum():
    """Testing py_back.enum.StrEnum."""
    from py_back import enum

    class Animal(enum.StrEnum):
        DOG = enum.auto()
        CAT = "cat"
        PLATYPUS = enum.auto()

    for pet in Animal:
        assert isinstance(pet, str), "Type not defined correctly"
        assert pet.upper() == str(pet).upper(), "str builtin functions are not working"

    assert list(Animal) == ["dog", "cat", "platypus"], "Formatting not working"
