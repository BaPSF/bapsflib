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
A package of relevant LaPD parameters and constants.
"""
__all__ = ['constants', 'port_spacing', 'ref_port']

from . import constants
from .constants import (port_spacing, ref_port)
