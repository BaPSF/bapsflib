"""
The `bapsflib.faux` module contains functionality to generate fake /
faux BaPSF style HDF5 files.

.. caution::
    The faux functionality is developed to test the `bapsflib` package
    and help in generating example documnetion.  It is **NOT** intended
    for end user use.

"""

__all__ = ["FauxHDFBuilder"]

from bapsflib.faux.builder import FauxHDFBuilder
