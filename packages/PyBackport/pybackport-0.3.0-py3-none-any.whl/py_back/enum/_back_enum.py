"""Backported enum types. Each class defines from which python version it was backported."""

from __future__ import annotations

import enum

from py_back import builtins

__all__ = ["EnumType", "IntEnum", "IntFlag", "ReprEnum", "StrEnum"]

# New in Python 3.11
EnumType = enum.EnumMeta


class ReprEnum(enum.Enum):
    """Updates 'repr', leaving 'str' and 'format' to the builtin class.

    Backported from py3.11.
    """

    def __str__(self) -> str:
        """String through the builtin class."""
        return self.value.__str__()

    def __format__(self, format_spec: str) -> str:
        """Format through the builtin class."""
        return self.value.__format__(format_spec)


class IntEnum(ReprEnum, enum.IntEnum):
    """Enum where members are also (and must be) ints.

    Backported from py3.11 leaving the str & format to the builtin class.
    """


class IntFlag(ReprEnum, enum.IntFlag):
    """Support for integer-based Flags.

    Backported from py3.11 leaving the str & format to the builtin class.
    """


class StrEnum(builtins.str, ReprEnum):
    """Enum where members are also (and must be) strings.

    Backported from py3.11.
    """

    def __new__(cls, *values) -> StrEnum:
        """Create new StrEnum.

        Method copied from original enum.StrEnum code.
        Values must already be of type `str`.
        """
        if len(values) > 3:
            raise TypeError(f"Too many arguments for str(): {values}")
        if len(values) == 1 and not isinstance(values[0], str):
            # Must be a string.
            raise TypeError(f"{values[0]} is not a string")
        if len(values) >= 2 and not isinstance(values[1], str):
            # check that encoding argument is a string
            raise TypeError(f"Encoding must be a string, not {values[1]}")
        if len(values) == 3 and not isinstance(values[2], str):
            # check that errors argument is a string
            raise TypeError(f"Errors must be a string, not {values[2]}")
        value = str(*values)
        new_member = str.__new__(cls, value)
        new_member._value_ = value
        return new_member

    @staticmethod
    def _generate_next_value_(name: str, *_) -> str:
        """Return the lower-cased version of the member name."""
        return name.lower()
