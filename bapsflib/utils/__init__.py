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
__all__ = ['BaPSFConstant', 'errors', 'temperature_and_energy',
           'warnings']

from . import (errors, warnings)
from .units import temperature_and_energy
from astropy.constants import Constant


class BaPSFConstant(Constant):
    """Factory Class for BaPSF Constants"""
    default_reference = 'Basic Plasma Facility'
    _registry = {}
    _has_incompatible_units = set()
