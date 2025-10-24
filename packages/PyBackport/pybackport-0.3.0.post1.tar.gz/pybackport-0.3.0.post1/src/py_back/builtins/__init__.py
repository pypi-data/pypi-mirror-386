"""Module to backport 'builtins' classes depending on the system python."""

import sys
import warnings
from builtins import *  # noqa: F403

__all__ = [name for name in dir() if not name.startswith("_")]

if sys.version_info >= (3, 9):
    warnings.warn(
        "Importing from the standard builtins library: dict, str\n"
        "Consider 'from builtins import ...' instead of 'from py_back.builtins "
        "import ...'",
        stacklevel=2,
    )
else:
    from ._back_builtins import dict, str  # noqa: F401, A004
