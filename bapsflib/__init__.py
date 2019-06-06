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
This is the bapsflib package, a Python toolkit designed for the Basic
Plasma Science Facility (BaPSF) group at the University of California,
Los Angeles (UCLA).

BaPSF Home:
http://plasma.physics.ucla.edu/

bapsflib Repository:
https://github.com/rocco8773/bapsflib
"""
# --- Public API -------------------------------------------------------

from . import _hdf
from . import lapd
from . import plasma

# --- Define version ---------------------------------------------------
__version__ = '1.0.1'
