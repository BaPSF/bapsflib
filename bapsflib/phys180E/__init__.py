"""
The `bapsflib.phys180E` sub-package contains functionality to aid in
accessing, reading, and manipulating the data recorded by devices in the
UCLA Physics 180E class.
"""

__all__ = ["File"]

from bapsflib.phys180E._hdf.file_ import File
