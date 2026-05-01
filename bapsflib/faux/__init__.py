"""
.. caution::
    The faux functionality is developed to test the `bapsflib` package
    and help in generating example documnetion.  It is **NOT** intended
    for end user use.

The `bapsflib.faux` module contains functionality to generate fake /
faux BaPSF style HDF5 files.

`bapsflib.faux` is not explicitly exposed to the `bapsflib` namespace,
so it needs to be explicitly imported.  For example:

>>> import bapsflib
>>> bapsflib.faux
AttributeError: module 'bapsflib' has no attribute 'faux'
>>>
>>> import bapsflib.faux
>>> bapsflib.faux
<module 'bapsflib.faux'>

"""

__all__ = ["FauxHDFBuilder"]

from bapsflib.faux import controls, digitizers, msi
from bapsflib.faux.builder import FauxHDFBuilder
