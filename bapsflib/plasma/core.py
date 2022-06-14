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
__all__ = [
    "AMU",
    "C",
    "cs",
    "E",
    "fce",
    "fci",
    "fLH",
    "FloatUnit",
    "fpe",
    "fpi",
    "fUH",
    "IntUnit",
    "KB",
    "lD",
    "lpe",
    "lpi",
    "ME",
    "MP",
    "oce",
    "oci",
    "oLH",
    "ope",
    "opi",
    "oUH",
    "rce",
    "rci",
    "VA",
    "vTe",
    "vTi",
]

import math

from scipy import constants

pconst = constants.physical_constants


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


#: atomic mass unit (g)
AMU = FloatUnit(1000.0 * constants.m_u, "g")

#: speed of light (cm/s)
C = FloatUnit(100.0 * constants.c, "cm s^-1")

#: fundamental charge (statcoul)
E = FloatUnit(4.8032e-10, "statcoul")

#: Boltzmann constant (erg/K)
KB = FloatUnit(1.3807e-16, "erg k^-1")

#: electron mass (g)
ME = FloatUnit(1000.0 * constants.m_e, "g")

#: proton mass (g)
MP = FloatUnit(1000.0 * constants.m_p, "g")


# ---- frequency constants ----
def fce(Bo, **kwargs):
    """
    electron-cyclotron frequency (Hz)

    .. math::

        f_{ce} = \\frac{\Omega_{ce}}{2 \pi}
        = -\\frac{|e| B_{o}}{2 \pi m_{e} c}

    :param float Bo: magnetic field (in Gauss)

    .. note:: see function :func:`oce`
    """
    _fce = oce(Bo) / (2.0 * math.pi)
    return FloatUnit(_fce, "Hz")


def fci(Bo, m_i, Z, **kwargs):
    """
    ion-cyclotron frequency (Hz)

    .. math::

        f_{ci} = \\frac{\Omega_{ci}}{2 \pi}
        = \\frac{Z |e| B_{o}}{2 \pi m_{i} c}

    :param float Bo: magnetic-field (in Gauss)
    :param float m_i: ion-mass (in g)
    :param int Z: charge number

    .. note:: see function :func:`oci`
    """
    _fci = oci(Bo, m_i, Z) / (2.0 * constants.pi)
    return FloatUnit(_fci, "Hz")


def fLH(Bo, m_i, n_i, Z, **kwargs):
    """
    Lower-Hybrid Resonance frequency (Hz)

    .. math::
        f_{LH} = \\frac{\omega_{LH}}{2 \pi}

    :param float Bo: magnetic field (in Gauss)
    :param float m_i: ion mass (in g)
    :param float n_i: ion number density (in :math:`cm^{-3}`)
    :param int Z: ion charge number

    .. note:: for details see function :func:`oLH`
    """
    _fLH = oLH(Bo, m_i, n_i, Z) / (2.0 * math.pi)
    return FloatUnit(_fLH, "Hz")


def fpe(n_e, **kwargs):
    """
    electron-plasma frequency (Hz)

    .. math::

        f_{pe} = \\frac{\omega_{pe}}{2 \pi}
        = \sqrt{\\frac{n_{e} e^{2}}{\pi m_{e}}}

    :param float n_e: electron number density (in :math:`cm^{-3}`)

    .. note:: see function :func:`ope`
    """
    _fpe = ope(n_e) / (2.0 * math.pi)
    return FloatUnit(_fpe, "Hz")


def fpi(m_i, n_i, Z, **kwargs):
    """
    ion-plasma frequency (Hz)

    .. math::

        f_{pi} = \\frac{\omega_{pi}}{2 \pi}
        = \sqrt{\\frac{n_{i} (Z e)^{2}}{\pi m_{i}}}

    :param float m_i: ion mass (in g)
    :param float n_i: ion number density (in :math:`cm^{-3}`)
    :param int Z: ion charge number

    .. note:: see function :func:`opi`
    """
    _fpi = opi(m_i, n_i, Z) / (2.0 * math.pi)
    return FloatUnit(_fpi, "Hz")


def fUH(Bo, n_e, **kwargs):
    """
    Upper-Hybrid Resonance frequency (Hz)

    .. math::

        f_{UH} = \\frac{\omega_{UH}}{2 \pi}

    :param float Bo: magnetic field (in Gauss)
    :param float n_e: electron number density (in :math:`cm^{-3}`)

    .. note:: see function :func:`oUH`
    """
    _fUH = oUH(Bo, n_e) / (2.0 * math.pi)
    return FloatUnit(_fUH, "Hz")


def oce(Bo, **kwargs):
    """
    electron-cyclotron frequency (rad/s)

    .. math::

        \Omega_{ce} = -\\frac{|e| B_{o}}{m_{e} c}

    :param float Bo: magnetic-field (in Gauss)
    """
    _oce = (-E * Bo) / (ME * C)
    return FloatUnit(_oce, "rad s^-1")


def oci(Bo, m_i, Z, **kwargs):
    """
    ion-cyclotron frequency (rads / s)

    .. math::

        \Omega_{ci} = \\frac{Z |e| B_{o}}{m_{i} c}

    :param float Bo: magnetic-field (in Gauss)
    :param float m_i: ion-mass (in g)
    :param int Z: charge number
    """
    _oci = (Z * E * Bo) / (m_i * C)
    return FloatUnit(_oci, "rad s^-1")


def oLH(Bo, m_i, n_i, Z, **kwargs):
    """
    Lower-Hybrid Resonance frequency (rad/s)

    .. math::
        \\frac{1}{\omega_{LH}^{2}}=
        \\frac{1}{\Omega_{i}^{2}+\omega_{pi}^{2}}
        + \\frac{1}{\\lvert \Omega_{e}\Omega_{i} \\rvert}

    .. note::

        This form is for a quasi-neutral plasma that satisfies

        .. math::
            \\frac{Z m_{e}}{m_{i}} \ll
            1 - \\left(\\frac{V_{A}}{c}\\right)^{2}

    :param float Bo: magnetic field (in Gauss)
    :param float m_i: ion mass (in g)
    :param float n_i: ion number density (in :math:`cm^{-3}`)
    :param int Z: ion charge number
    """
    _args = {"Bo": Bo, "m_i": m_i, "n_i": n_i, "Z": Z}
    _opi = opi(**_args)
    _oce = oce(**_args)
    _oci = oci(**_args)
    first_term = 1.0 / ((_oci**2) + (_opi**2))
    second_term = 1.0 / math.fabs(_oce * _oci)
    _olh = math.sqrt(1.0 / (first_term + second_term))
    return FloatUnit(_olh, "rad s^-1")


def ope(n_e, **kwargs):
    """
    electron-plasma frequency (in rad/s)

    .. math::

        \omega_{pe}^{2} = \\frac{4 \pi n_{e} e^2}{m_{e}}

    :param float n_e: electron number density (in :math:`cm^{-3}`)
    """
    _ope = math.sqrt(4 * math.pi * n_e * E * E / ME)
    return FloatUnit(_ope, "rad s^-1")


def opi(m_i, n_i, Z, **kwargs):
    """
    ion-plasma frequency (in rad/s)

    .. math::

        \omega_{pi}^{2} = \\frac{4 \pi n_{i} (Z e)^{2}}{m_{i}}

    :param float m_i: ion mass (in g)
    :param float n_i: ion number density (in :math:`cm^{-3}`)
    :param int Z: ion charge number
    """
    _opi = math.sqrt(4 * math.pi * n_i * (Z * E) * (Z * E) / m_i)
    return FloatUnit(_opi, "rad s^-1")


def oUH(Bo, n_e, **kwargs):
    """
    Upper-Hybrid Resonance frequency (rad/s)

    .. math::

        \omega_{UH}^{2} =\omega_{pe}^{2} + \Omega_{ce}^{2}

    :param float Bo: magnetic field (in Gauss)
    :param float n_e: electron number density (in :math:`cm^{-3}`)
    """
    _ope = ope(n_e)
    _oce = oce(Bo)
    _ouh = math.sqrt((_ope**2) + (_oce**2))
    return FloatUnit(_ouh, "rad s^-1")


# ---- length constants ----
def lD(kT, n, **kwargs):
    """
    Debye Length (in cm)

    .. math::

        \lambda_{D} = \sqrt{\\frac{k_{B} T}{4 \pi n e^{2}}}

    :param float kT: temperature (in eV)
    :param float n: number density (in :math:`cm^{-3}`)
    """
    kT = kT * constants.e * 1.0e7  # eV to ergs
    _lD = math.sqrt(kT / (4.0 * math.pi * n)) / E
    return FloatUnit(_lD, "cm")


def lpe(n_e, **kwargs):
    """
    electron-inertial length (cm)

    .. math::

        l_{pe} = \\frac{c}{\omega_{pe}}

    :param float n_e: electron number density (in :math:`cm^{-3}`)

    .. note:: see function :func:`ope`
    """
    _lpe = C / ope(n_e)
    return FloatUnit(_lpe, "cm")


def lpi(m_i, n_i, Z, **kwargs):
    """
    ion-inertial length (cm)

    .. math::

        l_{pi} = \\frac{c}{\omega_{pi}}

    :param float m_i: ion mass (in g)
    :param float n_i: ion number density (in :math:`cm^{-3}`)
    :param int Z: ion charge number

    .. note:: see function :func:`opi`
    """
    _lpi = C / opi(m_i, n_i, Z)
    return FloatUnit(_lpi, "cm")


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
    return FloatUnit(_rce, "cm")


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
    return FloatUnit(_rci, "cm")


# ---- velocity constants ----
def cs(kTe, m_i, Z, gamma=1.0, **kwargs):
    """
    ion sound speed (cm/s)

    .. math::

        C_{s} = \sqrt{\\frac{\gamma Z k T_{e}}{m_{i}}}

    .. note::

        :math:`\gamma=1` for the case of :math:`T_{i}\ll T_{e}`
        (DEFAULT)

    :param float kTe: electron temperature (in eV)
    :param float m_i: ion mass (in g)
    :param int Z: charge number
    :param float gamma: adiabatic index
    """
    # TODO: double check adiabatic index default value
    kTe = kTe * constants.e * 1.0e7  # eV to ergs
    _cs = math.sqrt(gamma * Z * kTe / m_i)
    return FloatUnit(_cs, "cm s^-1")


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
    return FloatUnit(_VA, "cm s^-1")


def vTe(kTe, **kwargs):
    """
    electron thermal velocity (in cm/s)

    .. math::

        v_{T_{e}} = \sqrt{\\frac{k T_{e}}{m_{e}}}

    :param float kTe: electron temperature (in eV)
    """
    kTe = kTe * constants.e * 1.0e7  # eV to erg
    _vTe = math.sqrt(kTe / ME)
    return FloatUnit(_vTe, "cm s^-1")


def vTi(kTi, m_i, **kwargs):
    """
    ion thermal velocity (in cm/s)

    .. math::

        v_{T_{i}} = \sqrt{\\frac{k T_{i}}{m_{i}}}

    :param float kTi: ion temperature (in eV)
    :param float m_i: ion mass (in g)
    """
    kTi = kTi * constants.e * 1.0e7  # eV to erg
    _vTi = math.sqrt(kTi / m_i)
    return FloatUnit(_vTi, "cm s^-1")
