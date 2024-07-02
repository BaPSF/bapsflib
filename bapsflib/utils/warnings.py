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
"""Warnings specific to `bapsflib`."""
__all__ = ["BaPSFWarning", "HDFMappingWarning"]


class BaPSFWarning(Warning):
    """
    Base class of BaPSF custom warnings.

    All BaPSF custom warnings should inherit from this class and be
    defined in this module.
    """


class _HDFWarning(BaPSFWarning):
    """
    Base warning for `bapsflib` interactions with HDF5 files, reading,
    mapping, etc.
    """


class HDFMappingWarning(_HDFWarning):
    """Warning for HDF5 mappings."""
