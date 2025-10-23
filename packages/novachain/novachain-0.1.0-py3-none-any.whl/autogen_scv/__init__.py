from __future__ import annotations
import warnings as _w
from novachain import *  # re-export

_w.warn(
    "The 'autogen_scv' package has been renamed to 'novachain'. "
    "Please update your imports.",
    DeprecationWarning,
    stacklevel=2,
)
