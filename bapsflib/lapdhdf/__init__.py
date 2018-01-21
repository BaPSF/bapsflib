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
The :mod:`bapsflib.lapdhdf` module contains the necessary tools to
open (:class:`~bapsflib.lapdhdf.files.File`),
map (:class:`~bapsflib.lapdhdf.hdfmappers.hdfMap`),
check, (:class:`~bapsflib.lapdhdf.hdfchecks.hdfCheck`)
and read out (:meth:`~bapsflib.lapdhdf.files.File.read_data` and
:meth:`~bapsflib.lapdhdf.files.File.read_controls`)
data written into HDF5 files generated by the LaPD DAQ system.
"""
from .files import File
