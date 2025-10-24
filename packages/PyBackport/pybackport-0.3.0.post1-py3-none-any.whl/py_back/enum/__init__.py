"""Module to backport 'enum' classes depending on the system python."""

import sys
import warnings
from enum import Enum, EnumMeta, Flag, auto, unique

__all__ = ["Enum", "EnumMeta", "EnumType", "Flag", "IntEnum", "IntFlag", "ReprEnum", "StrEnum", "auto", "unique"]

if sys.version_info >= (3, 11):
    from enum import EnumType, IntEnum, IntFlag, ReprEnum, StrEnum

    warnings.warn(
        "Importing from the standard enum library: "
        "EnumType, IntEnum, IntFlag, ReprEnum, StrEnum\n"
        "Consider 'from enum import ...' instead of 'from py_back.enum "
        "import ...'",
        stacklevel=2,
    )
else:
    from ._back_enum import EnumType, IntEnum, IntFlag, ReprEnum, StrEnum
