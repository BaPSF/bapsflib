# This file is part of the bapsflib package, a Python toolkit for the
# BaPSF group at UCLA.
#
# http://plasma.physics.ucla.edu/
#
# Copyright 2017-2020 Erik T. Everson and contributors
#
# License: Standard 3-clause BSD; see "LICENSES/LICENSE.txt" for full
#   license terms and contributor agreement.
#
"""
Sub-package containing the "high-level" architecture for accessing and
mapping the HDF5 files generated at BaPSF.
"""
__all__ = ["ConType", "File", "HDFMap"]

from bapsflib._hdf import maps, utils
from bapsflib._hdf.maps import ConType, HDFMap
from bapsflib._hdf.utils.file import File
