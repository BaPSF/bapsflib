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
"""Exceptions specific to `bapsflib`."""
__all__ = [
    "BaPSFError",
    "HDFMappingError",
    "HDFReadControlError",
    "HDFReadDigiError",
    "HDFReadMSIError",
    "HDFReadError",
]


class BaPSFError(Exception):
    """
    Base class of BaPSF custom exceptions.

    All custom exceptions raised by `bapsflib` should inherit from this
    class and be defined in this module.
    """


class _HDFError(BaPSFError):
    """
    Base exception for `bapsflib` interactions with HDF5 files, reading,
    mapping, etc.
    """


class HDFMappingError(_HDFError):
    """Exception for failed HDF5 mappings"""

    def __init__(self, device_name: str, why=""):
        super().__init__(f"'{device_name}' mapping failed: {why}")


class HDFReadError(_HDFError):
    """Exception for failed HDF5 reading"""


class HDFReadDigiError(HDFReadError):
    """Exception for failed HDF5 reading of digitizer."""


class HDFReadControlError(HDFReadError):
    """Exception for failed HDF5 reading of digitizer."""


class HDFReadMSIError(HDFReadError):
    """Exception for failed HDF5 reading of digitizer."""
