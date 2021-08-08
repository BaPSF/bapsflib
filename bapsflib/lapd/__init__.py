# This file is part of the bapsflib package, a Python toolkit for the
# BaPSF group at UCLA.
#
# http://plasma.physics.ucla.edu/
#
# Copyright 2017-2018 Erik T. Everson and contributors
#
# License: Standard 3-clause BSD; see "LICENSES/LICENSE.txt" for full
#   license terms and contributor agreement.
#
"""
The :mod:`bapsflib.lapd` sub-package contains the necessary tools to access
data relevant to and collected on the LaPD.  The
:mod:`~bapsflib.lapd._hdf` package focuses on accessing and reading
data written to HDF5 files. The :mod:`~bapsflib.lapd.constants` package
contains constants relevant to the LaPD configuration (e.g. cathode
diameters, port spacing, etc.).  The :mod:`~bapsflib.lapd.tools` package
contains functions and classes relevant for calculating LaPD parameters
(e.g. converting port number to axial z location, etc.).
"""
__all__ = ["ConType", "File"]

from bapsflib._hdf.maps.controls.types import ConType
from bapsflib.lapd import _hdf, constants, tools
from bapsflib.lapd._hdf.file import File
