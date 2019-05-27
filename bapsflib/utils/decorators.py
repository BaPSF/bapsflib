# This file is part of the bapsflib package, a Python toolkit for the
# BaPSF group at UCLA.
#
# http://plasma.physics.ucla.edu/
#
# Copyright 2017-2019 Erik T. Everson and contributors
#
# License: Standard 3-clause BSD; see "LICENSES/LICENSE.txt" for full
#   license terms and contributor agreement.
#
"""
Decorators for the :mod:`bapsflib` package.
"""
__all__ = ['with_bf', 'with_lapdf']

from functools import wraps


def with_bf(func):
    """
    Context decorator for managing the opening and closing BaPSF HDF5
    Files :class:`bapsflib._hdf.utils.file.File`.  Intended for use on
    test methods.
    """
    # TODO: let with_bf args define control_path, digitzer_path, msi_path
    from bapsflib._hdf import File

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        with File(self.f.filename,
                  control_path='Raw data + config',
                  digitizer_path='Raw data + config',
                  msi_path='MSI') as bf:
            return func(self, bf, *args, **kwargs)
    return wrapper


def with_lapdf(func):
    """
    Context decorator for managing the opening and closing LaPD HDF5
    Files :class:`bapsflib.lapd._hdf.file.File`.  Intended for use on
    test methods.
    """
    from bapsflib.lapd import File

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        with File(self.f.filename) as lapdf:
            return func(self, lapdf, *args, *kwargs)
    return wrapper
