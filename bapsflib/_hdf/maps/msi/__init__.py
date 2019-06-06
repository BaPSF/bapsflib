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
(:class:`~.map_msi.HDFMapMSI`).
"""
__all__ = ['discharge', 'gaspressure', 'heater', 'HDFMapMSI',
           'interferometerarray', 'magneticfield', 'map_msi',
           'templates']

from . import (discharge, gaspressure, heater, interferometerarray,
               magneticfield, map_msi, templates)
from .map_msi import HDFMapMSI
