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
Package of developer utilities.
"""
__all__ = ['decorators', 'errors', 'warnings']

from . import (decorators, errors, warnings)


def NdarrayToXarray(data, name={}):
    names = list(data.dtype.names)
    names.remove('signal')
    i=0
    while i<len(names):
        print(names[i])
        i = i+1
    return x
