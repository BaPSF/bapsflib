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

import astropy.constants as const
import astropy.units as u
import math

from scipy import constants

#pconst = constants.physical_constants

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
'''
# ---- length constants ----
def rce(Bo, kTe, **kwargs):
    """
    electron gyroradius (cm)

    .. math::

        r_{ce} = \\frac{v_{T_{e}}}{\Omega_{ce}}

    :param float Bo: magnetic field (in Gauss)
    :param float kTe: electron temperature (in eV)

    .. note:: see functions :func:`vTe` and :func:`oce`
    """
    _rce = vTe(kTe) / abs(oce(Bo))
    return FloatUnit(_rce, 'cm')


def rci(Bo, kTi, m_i, Z, **kwargs):
    """
    ion gyroradius (cm)

    .. math::

        r_{ci} = \\frac{v_{T_{i}}}{\Omega_{ci}}

    :param float Bo: magnetic field (in Gauss)
    :param float kTi: ion temperature (in eV)
    :param float m_i: ion mass (in g)
    :param int Z: ion charge number

    .. note:: see functions :func:`vTi` and :func:`oci`
    """
    _rci = vTi(kTi, m_i) / oci(Bo, m_i, Z)
    return FloatUnit(_rci, 'cm')


# ---- velocity constants ----
def VA(Bo, m_i, n_i, **kwargs):
    """
    Alfvén Velocity (in cm/s)

    .. math::

        V_{A} = \\frac{B_{o}}{\sqrt{4 \pi n_{i} m_{i}}}

    :param float Bo: magnetic field (in Gauss)
    :param float m_i: ion mass (in g)
    :param float n_i: ion number density (in :math:`cm^{-3}`)
    """
    _VA = Bo / math.sqrt(4.0 * math.pi * n_i * m_i)
    return FloatUnit(_VA, 'cm s^-1')


def vTe(kTe, **kwargs):
    """
    electron thermal velocity (in cm/s)

    .. math::

        v_{T_{e}} = \sqrt{\\frac{k T_{e}}{m_{e}}}

    :param float kTe: electron temperature (in eV)
    """
    kTe = kTe * constants.e * 1.e7  # eV to erg
    _vTe = math.sqrt(kTe / ME)
    return FloatUnit(_vTe, 'cm s^-1')


def vTi(kTi, m_i, **kwargs):
    """
    ion thermal velocity (in cm/s)

    .. math::

        v_{T_{i}} = \sqrt{\\frac{k T_{i}}{m_{i}}}

    :param float kTi: ion temperature (in eV)
    :param float m_i: ion mass (in g)
    """
    kTi = kTi * constants.e * 1.e7 # eV to erg
    _vTi = math.sqrt(kTi / m_i)
    return FloatUnit(_vTi, 'cm s^-1')
'''
