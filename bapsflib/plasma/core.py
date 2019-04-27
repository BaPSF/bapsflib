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
# TODO: add plasma betas (electron, ion, and total)
# TODO: add Coulomb Logarithm
# TODO: add collision frequencies
# TODO: add mean-free-paths
#
"""Core plasma parameters in (cgs)."""

'''
class FloatUnit(float):
    """Template class for floats with a unit attribute."""

    def __new__(cls, value, cgs_unit):
        """
        :param float value: value of constant
        :param str cgs_unit: string representation of of cgs unit
        :return: value of constant
        :rtype: float
        """
        obj = super().__new__(cls, value)
        obj._unit = cgs_unit
        return obj

    def __init__(self, value, cgs_unit):
        super().__init__()

    @property
    def unit(self):
        """units of constant"""
        return self._unit


class IntUnit(int):
    """Template class for ints with a unit attribute."""

    def __new__(cls, value, cgs_unit):
        """
        :param int value: value of constant
        :param str cgs_unit: string representation of of cgs unit
        :return: value of constant
        :rtype: int
        """
        obj = super().__new__(cls, value)
        obj._unit = cgs_unit
        return obj

    def __init__(self, value, cgs_unit):
        super().__init__()

    @property
    def unit(self):
        """units of constant"""
        return self._unit
'''
