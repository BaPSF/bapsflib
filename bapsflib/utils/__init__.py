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
from . import (errors, warnings)
from astropy.constants import Constant

__all__ = ['BaPSFConstant', 'errors', 'warnings']


class BaPSFConstant(Constant):
    """Factory Class for BaPSF Constants"""
    default_reference = 'Basic Plasma Facility'
    _registry = {}
    _has_incompatible_units = set()
