# This file is part of the bapsflib package, a Python toolkit for the
# BaPSF group at UCLA.
#
# http://plasma.physics.ucla.edu/
#
# Copyright 2017 Erik T. Everson and contributors
#
# License: Standard 3-clause BSD; see "LICENSES/LICENSE.txt" for full
#   license terms and contributor agreement.
#
"""Core plasma paramters in (cgs)."""

import math

from scipy import constants

pconst = constants.physical_constants


class ConstantTemplate(float):
    """Template class for constants"""
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
        """units of of constant"""
        return self._unit


AMU = ConstantTemplate(1000.0 * constants.m_u, 'g')  # atomic mass unit
C = ConstantTemplate(10.0 * constants.c, 'cm s^-1')  # speed of light
E = ConstantTemplate(4.8032e-10, 'statcoul')  # fundamental charge
KB = ConstantTemplate(1.3807e-16, 'erg k^-1')  # Boltzmann constant
ME = ConstantTemplate(1000.0 * constants.m_e, 'g')  # electron mass
MP = ConstantTemplate(1000.0 * constants.m_p, 'g')  # proton mass


def fce(Bo):
    """
    electron-cyclotron frequency (Hz)

    :param float Bo: magnetic field (in Gauss)
    """
    _fce = oce(Bo) / (2.0 * math.pi)
    return ConstantTemplate(_fce, 'Hz')


def fci(Z, Bo, m_i):
    """
    ion-cyclotron frequency (Hz)

    :param int Z: charge number
    :param float Bo: magnetic-field (in Gauss)
    :param float m_i: ion-mass (in g)
    """
    _fci = oci(Z, Bo, m_i) / (2.0 * constants.pi)
    return ConstantTemplate(_fci, 'Hz')


def fpe(n_e):
    """
    electron-plasma frequency (Hz)

    :param float n_e: electron number density (in cm^-3)
    """
    _fpe = ope(n_e) / (2.0 * math.pi)
    return ConstantTemplate(_fpe, 'Hz')


def fpi(Z, n_i, m_i):
    """
    ion-plasma frequency (Hz)

    :param Z: ion charge number
    :param float n_i: ion number density (in cm^-3)
    :param float m_i: ion mass (in g)
    """
    _fpi = opi(Z, n_i, m_i) / (2.0 * math.pi)
    return ConstantTemplate(_fpi, 'Hz')


def oce(Bo):
    """
    electron-cyclotron frequency (rad/s)

    :param float Bo: magnetic-field (in Gauss)
    :return: electorn-cyclotron frequency (in rad/s)
    :rtype: float
    """
    _oce = (E * Bo) / (ME * C)
    return ConstantTemplate(_oce, 'rad s^-1')


def oci(Z, Bo, m_i):
    """
    ion-cyclotron frequency (rads / s)

    :param int Z: charge number
    :param float Bo: magnetic-field (in Gauss)
    :param float m_i: ion-mass (in g)
    :return: ion-cyclotron frequency (in rads / s)
    :rtype: float
    """
    _oci = (Z * E * Bo) / (m_i * C)
    return ConstantTemplate(_oci, 'rad s^-1')


def ope(n_e):
    """
    electron-plasma frequency (in rad/s)

    :param float n_e: electron number density (in cm^-3)
    :return: electron-plasma frequency (in rad/s)
    :rtype: float
    """
    _ope = math.sqrt(4 * math.pi * n_e * E * E / ME)
    return ConstantTemplate(_ope, 'rad s^-1')


def opi(Z, n_i, m_i):
    """
    ion-plasma frequency (in rad/s)

    :param Z: ion charge number
    :param float n_i: ion number density (in cm^-3)
    :param float m_i: ion mass (in g)
    :return: ion-plasma frequency (in rad/s)
    :rtype: float
    """
    _opi = math.sqrt(4 * math.pi * n_i * (Z * E) * (Z * E) / m_i)
    return ConstantTemplate(_opi, 'rad s^-1')
