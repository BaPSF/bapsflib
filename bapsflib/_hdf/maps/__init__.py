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
This package contains an assortment of mapping classes used to inspect
and map the various HDF5 files generated during experiments at the
Basic Plasma Science Facility.  Sub-package
:mod:`~.controls` contains routines for mapping
:ibf:`Control Device` HDF5 groups,
:mod:`~.digitizers` contains routines for
mapping :ibf:`Digitizer` HDF5 groups, and
:mod:`~.msi` contains routines for mapping
:ibf:`MSI Diagnostic` HDF5 groups.
"""
__all__ = ['ConType', 'FauxHDFBuilder', 'hdfmap', 'HDFMap',
           'HDFMapControls', 'HDFMapDigitizers', 'HDFMapMSI']

from . import hdfmap
from .controls import (ConType, HDFMapControls)
from .digitizers import HDFMapDigitizers
from .hdfmap import HDFMap
from .msi import HDFMapMSI
from .tests.fauxhdfbuilder import FauxHDFBuilder
