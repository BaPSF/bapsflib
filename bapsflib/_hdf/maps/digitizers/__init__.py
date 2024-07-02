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
Package of digitizer mapping classes and their constructor
(:class:`~.map_digis.HDFMapDigitizers`).
"""
__all__ = ["HDFMapDigitizers"]

from bapsflib._hdf.maps.digitizers import map_digis, sis3301, siscrate, templates
from bapsflib._hdf.maps.digitizers.map_digis import HDFMapDigitizers
