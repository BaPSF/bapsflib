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
__all__ = []

from typing import Union

from bapsflib.utils import decorators, exceptions, warnings


def _bytes_to_str(string: Union[bytes, str]) -> str:
    """Helper to convert a bytes literal to a utf-8 string."""
    if isinstance(string, str):
        return string

    if isinstance(string, bytes):
        try:
            return str(string, "utf-8")
        except UnicodeDecodeError:
            return str(string, "cp1252")

    raise TypeError(f"Argument 'string' is not of type str or bytes, got {type(string)}.")
