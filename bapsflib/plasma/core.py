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
# TODO: add lower-hybrid resonance
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
        """units of constant"""
        return self._unit


#: atomic mass unit (g)
AMU = ConstantTemplate(1000.0 * constants.m_u, 'g')

#: speed of light (cm/s)
C = ConstantTemplate(100.0 * constants.c, 'cm s^-1')

#: fundamental charge (statcoul)
E = ConstantTemplate(4.8032e-10, 'statcoul')

#: Boltzmann constant (erg/K)
KB = ConstantTemplate(1.3807e-16, 'erg k^-1')

#: electron mass (g)
ME = ConstantTemplate(1000.0 * constants.m_e, 'g')

#: proton mass (g)
MP = ConstantTemplate(1000.0 * constants.m_p, 'g')


# ---- frequency constants ----
def fce(Bo):
    """
    electron-cyclotron frequency (Hz)

    .. math::

        f_{ce} = \Omega_{ce} / ( 2 \pi ) = e B_{o} / (2 \pi m_{e} c)

    :param float Bo: magnetic field (in Gauss)
    """
    _fce = oce(Bo) / (2.0 * math.pi)
    return ConstantTemplate(_fce, 'Hz')


def fci(Bo, m_i, Z):
    """
    ion-cyclotron frequency (Hz)

    .. math::

        f_{ci} = \Omega_{ci} / ( 2 \pi ) = Z e B_{o} / (2 \pi m_{i} c)

    :param float Bo: magnetic-field (in Gauss)
    :param float m_i: ion-mass (in g)
    :param int Z: charge number
    """
    _fci = oci(Z, Bo, m_i) / (2.0 * constants.pi)
    return ConstantTemplate(_fci, 'Hz')


def fpe(n_e):
    """
    electron-plasma frequency (Hz)

    .. math::

        f_{pe} &= \omega_{pe} / ( 2 \pi ) \\\\
               &= \sqrt{n_{e} e^{2} / (\pi m_{e})}

    :param float n_e: electron number density (in cm^-3)
    """
    _fpe = ope(n_e) / (2.0 * math.pi)
    return ConstantTemplate(_fpe, 'Hz')


def fpi(m_i, n_i, Z):
    """
    ion-plasma frequency (Hz)

    .. math::

        f_{pi} &= \omega_{pi} / ( 2 \pi ) \\\\
               &= \sqrt{n_{i} (Z e)^{2} / (\pi m_{i})}

    :param float m_i: ion mass (in g)
    :param float n_i: ion number density (in cm^-3)
    :param int Z: ion charge number
    """
    _fpi = opi(Z, n_i, m_i) / (2.0 * math.pi)
    return ConstantTemplate(_fpi, 'Hz')


def fUH(Bo, n_e):
    """
    Upper-Hybrid Resonance frequency (Hz)

    .. math::

        f_{UH} = \omega_{UH} / (2 \pi)

    :param float Bo: magnetic field (in Gauss)
    :param float n_e: electron numbeer density (in cm^-3)
    """
    _fUH = oUH(Bo, n_e) / (2.0 * math.pi)
    return ConstantTemplate(_fUH, 'Hz')

def oce(Bo):
    """
    electron-cyclotron frequency (rad/s)

    .. math::

        \Omega_{ce} = e B_{o} / (m_{e} c)

    :param float Bo: magnetic-field (in Gauss)
    """
    _oce = (E * Bo) / (ME * C)
    return ConstantTemplate(_oce, 'rad s^-1')


def oci(Bo, m_i, Z):
    """
    ion-cyclotron frequency (rads / s)

    .. math::

        \Omega_{ci} = Z e B_{o} / (m_{i} c)

    :param float Bo: magnetic-field (in Gauss)
    :param float m_i: ion-mass (in g)
    :param int Z: charge number
    """
    _oci = (Z * E * Bo) / (m_i * C)
    return ConstantTemplate(_oci, 'rad s^-1')


def ope(n_e):
    """
    electron-plasma frequency (in rad/s)

    .. math::

        \omega_{pe}^{2} = 4 \pi n_{e} e^2 / m_{e}

    :param float n_e: electron number density (in cm^-3)
    """
    _ope = math.sqrt(4 * math.pi * n_e * E * E / ME)
    return ConstantTemplate(_ope, 'rad s^-1')


def opi(m_i, n_i, Z):
    """
    ion-plasma frequency (in rad/s)

    .. math::

        \omega_{pi}^{2} = 4 \pi n_{i} (Z e)^{2} / m_{i}

    :param float m_i: ion mass (in g)
    :param float n_i: ion number density (in cm^-3)
    :param int Z: ion charge number
    """
    _opi = math.sqrt(4 * math.pi * n_i * (Z * E) * (Z * E) / m_i)
    return ConstantTemplate(_opi, 'rad s^-1')


def oUH(Bo, n_e):
    """
    Upper-Hybrid Resonance frequency (rad/s)

    .. math::

        \omega_{UH}^{2} =\omega_{pe}^{2} + \Omega_{ce}^{2}

    :param float Bo: magnetic field (in Gauss)
    :param float n_e: electron number density (in cm^-3)
    """
    _ope = ope(n_e)
    _oce = oce(Bo)
    _ouh = math.sqrt((_ope ** 2) + (_oce ** 2))
    return ConstantTemplate(_ouh, 'rad s^-1')


# ---- length constants ----
def lD(kT, n):
    """
    Debye Length (in cm)

    .. math::

        \lambda_{D} = \sqrt{k_{B} T / (4 \pi n e^{2})}

    :param float kT: temperature (in eV)
    :param float n: number density (in cm^-3)
    """
    kT = kT * constants.e * 1.e7  # eV to ergs
    _lD = math.sqrt(kT / (4.0 * math.pi * n)) / E
    return ConstantTemplate(_lD, 'cm')


def lpe(n_e):
    """
    electron-inertial length (cm)

    .. math::

        l_{pe} = c / \omega_{pe}

    :param float n_e: electron number density (in cm^-3)
    """
    _lpe = C / ope(n_e)
    return ConstantTemplate(_lpe, 'cm')


def lpi(m_i, n_i, Z):
    """
    ion-inertial length (cm)

    .. math::

        l_{pi} = c / \omega_{pi}

    :param float m_i: ion mass (in g)
    :param float n_i: ion number density (in cm^-3)
    :param int Z: ion charge number
    """
    _lpi = C / opi(Z, n_i, m_i)
    return ConstantTemplate(_lpi, 'cm')


def rce(Bo, kTe):
    """
    electron gyroradius (cm)

    .. math::

        r_{ce} = v_{T_{e}} / \Omega_{ce}

    :param float Bo: magnetic field (in Gauss)
    :param float kTe: electron temperature (in eV)
    """
    _rce = vTe(kTe) / oce(Bo)
    return ConstantTemplate(_rce, 'cm')


def rci(Bo, kTi, m_i, Z, **kwargs):
    """
    ion gyroradius (cm)

    .. math::

        r_{ci} = v_{T_{i}} / \Omega_{ci}

    :param float Bo: magnetic field (in Gauss)
    :param float kTi: ion temperature (in eV)
    :param float m_i: ion mass (in g)
    :param int Z: ion charge number
    """
    _rci = vTi(kTi, m_i) / oci(Z, Bo, m_i)
    return ConstantTemplate(_rci, 'cm')


# ---- velocity constants ----
def cs(kTe, m_i, Z, gamma=1.5):
    """
    ion sound speed (cm/s)

    .. math::

        C_{s} = \sqrt{\gamma Z k T_{e} / m_{i}}

    :param float kTe: electron temperature (in eV)
    :param float m_i: ion mass (in g)
    :param int Z: charge number
    :param float gamma: adiabatic index
    """
    # TODO: double check adiabatic index default value
    kTe = kTe * constants.e * 1.e7 # eV to ergs
    _cs = math.sqrt(gamma * Z * kTe / m_i)
    return ConstantTemplate(_cs, 'cm s^-1')


def VA(Bo, m_i, n_i):
    """
    Alfven Velocity (in cm/s)

    .. math::

        V_{A} = B_{o} / \sqrt{4 \pi n_{i} m_{i}}

    :param float Bo: magnetic field (in Gauss)
    :param float m_i: ion mass (in g)
    :param float n_i: ion number density (in cm^-3)
    """
    _VA = Bo / math.sqrt(4.0 * math.pi * n_i * m_i)
    return ConstantTemplate(_VA, 'cm s^-1')


def vTe(kTe):
    """
    electron thermal velocity (in cm/s)

    .. math::

        v_{T_{e}} = \sqrt{k T_{e} / m_{e}}

    :param float kTe: electron temperature (in eV)
    """
    kTe = kTe * constants.e * 1.e7 # eV to erg
    _vTe = math.sqrt(kTe / ME)
    return ConstantTemplate(_vTe, 'cm s^-1')


def vTi(kTi, m_i):
    """
    ion thermal velocity (in cm/s)

    .. math::

        v_{T_{i}} = \sqrt{k T_{i} / m_{i}}

    :param float kTi: ion temperature (in eV)
    :param float m_i: ion mass (in g)
    """
    kTi = kTi * constants.e * 1.e7 # eV to erg
    _vTi = math.sqrt(kTi / m_i)
    return ConstantTemplate(_vTi, 'cm s^-1')