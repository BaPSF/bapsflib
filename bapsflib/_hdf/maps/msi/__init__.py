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
Package of MSI diagnostic mapping classes and their constructor
(`~.map_msi.HDFMapMSI`).
"""
__all__ = ["HDFMapMSI"]

from bapsflib._hdf.maps.msi import (
    discharge,
    gaspressure,
    heater,
    interferometerarray,
    magneticfield,
    map_msi,
    templates,
)
from bapsflib._hdf.maps.msi.map_msi import HDFMapMSI
