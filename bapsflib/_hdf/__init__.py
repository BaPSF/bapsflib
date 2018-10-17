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
This package contains the mapping classes (in :mod:`~.maps`) and file
access classes (in :mod:`~.utils`) used to map and interface with the
HDF5 files generated at BaPSF.
"""
from .maps import (ConType, HDFMap)
from .utils.hdfreadmsi import HDFReadMSI
# from bapsflib._hdf.maps.controls import HDFMapControls
# from bapsflib._hdf.maps.digitizers import HDFMapDigitizers
# from bapsflib._hdf.maps.msi import HDFMapMSI

__all__ = ['ConType', 'HDFReadMSI', 'HDFMap']
