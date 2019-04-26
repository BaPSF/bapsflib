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
"""
Plasma parameters

All units are in Gaussian cgs except for temperature, which is
expressed in eV. (same as the NRL Plasma Formulary)
"""
import astropy.units as u
import numpy as np

from . import constants as const
from bapsflib.utils.errors import PhysicsError
from plasmapy import utils
from typing import Union


__all__ = ['cyclotron_frequency', 'oce', 'oci',
           'lower_hybrid_frequency', 'oLH',
           'plasma_frequency', 'ope', 'opi',
           'upper_hybrid_frequency', 'oUH',
           'Debye_length', 'lD',
           'inertial_length', 'lpe', 'lpi',
           'Alfven_speed', 'VA',
           'ion_sound_speed', 'cs']


# ---- Frequencies                                                  ----
@utils.check_quantity({'q': {'units': u.statcoulomb,
                             "can_be_negative": True},
                       'B': {'units': u.Gauss,
                             "can_be_negative": False},
                       'm': {'units': u.g,
                             "can_be_negative": False}})
def cyclotron_frequency(q: u.Quantity, B: u.Quantity, m: u.Quantity,
                        to_Hz=False, **kwargs) -> u.Quantity:
    """
    generalized cyclotron frequency (rad/s)

    .. math::

        \\Omega_{c} = \\frac{q B}{m c}

    :param q: particle charge (in statcoulomb)
    :param B: magnetic-field (in Gauss)
    :param m: particle mass (in grams)
    :param to_Hz: :code:`False` (DEFAULT). Set to :code:`True` to
        return frequency in Hz (i.e. divide by :math:`2 * \\pi`)
    """
    # ensure args have correct units
    q = q.to(u.Fr)
    B = B.to(u.gauss)
    m = m.to(u.g)

    # calculate
    _oc = ((q.value * B.value) / (m.value * const.c.cgs.value))
    if to_Hz:
        _oc = (_oc / (2.0 * const.pi)) * u.Hz
    else:
        _oc = _oc * (u.rad / u.s)
    return _oc


@utils.check_quantity({'B': {'units': u.gauss,
                             'can_be_negative': False},
                       'n_i': {'units': u.cm ** -3,
                               'can_be_negative': False},
                       'm_i': {'units': u.g,
                               'can_be_negative': False}})
def lower_hybrid_frequency(B: u.Quantity, n_i: u.Quantity,
                           m_i: u.Quantity, Z: Union[int, float] = 1,
                           to_Hz=False, **kwargs) -> u.Quantity:
    """
    Lower-Hybrid resonance Frequency (rad/s)

    .. math::
        \\frac{1}{\\omega_{LH}^{2}}=
        \\frac{1}{\\Omega_{ci}^{2}+\\omega_{pi}^{2}}
        + \\frac{1}{\\lvert \\Omega_{ce}\\Omega_{ci} \\rvert}

    .. note::

        This form is for a quasi-neutral plasma that satisfies

        .. math::
            \\frac{Z m_{e}}{m_{i}} \\ll
            1 - \\left(\\frac{V_{A}}{c}\\right)^{2}

    :param B: magnetic field (in Gauss)
    :param m_i: ion mass (in g)
    :param n_i: ion number density (in :math:`cm^{-3}`)
    :param Z: ion charge number (:math:`Z=1` DEFAULT)
    :param to_Hz: :code:`False` (DEFAULT). Set to :code:`True` to
        return frequency in Hz (i.e. divide by :math:`2 * \\pi`)
    """
    # condition Z
    if not isinstance(Z, (int, np.integer, float, np.floating)):
        raise TypeError('Z must be of type int or float')
    elif Z <= 0:
        raise PhysicsError(
            'The ion charge number Z must be greater than 0.')

    # calculate
    _oci = oci(B, m_i, Z=Z, to_Hz=to_Hz, **kwargs)
    _opi = opi(n_i, m_i, Z=Z, to_Hz=to_Hz, **kwargs)
    _oce = oce(B, to_Hz=to_Hz, **kwargs)
    first_term = 1.0 / ((_oci ** 2) + (_opi ** 2))
    second_term = 1.0 / np.abs(_oce * _oci)
    _olh = np.sqrt(1.0 / (first_term + second_term))
    return _olh

@utils.check_quantity({'B': {'units': u.Gauss,
                             "can_be_negative": False}})
def oce(B: u.Quantity, **kwargs) -> u.Quantity:
    """
    electron-cyclotron frequency (rad/s)

    .. math::

        \\Omega_{ce} = -\\frac{|e| B}{m_{e} c}

    :param B: magnetic-field (in Gauss)
    :param kwargs: supports any keywords used by
        :func:`cyclotron_frequency`
    """
    return cyclotron_frequency(-const.e_gauss, B, const.m_e.cgs,
                               **kwargs['kwargs'])


@utils.check_quantity({'B': {'units': u.Gauss,
                             "can_be_negative": False},
                       'm_i': {'units': u.g,
                               "can_be_negative": False}})
def oci(B: u.Quantity, m_i: u.Quantity, Z: Union[int, float] = 1,
        **kwargs) -> u.Quantity:
    """
    ion-cyclotron frequency (rad/s)

    .. math::

        \\Omega_{ci} = \\frac{Z |e| B}{m_{i} c}

    :param B: magnetic-field (in Gauss)
    :param m_i: ion mass (in grams)
    :param Z: ion charge number (:math:`Z=1` DEFAULT)
    :param kwargs: supports any keywords used by
        :func:`cyclotron_frequency`
    """
    # condition Z
    if not isinstance(Z, (int, np.integer, float, np.floating)):
        raise TypeError('Z must be of type int or float')
    elif Z <= 0:
        raise PhysicsError(
            'The ion charge number Z must be greater than 0.')

    return cyclotron_frequency(Z * const.e_gauss, B, m_i,
                               **kwargs['kwargs'])


def oLH(B: u.Quantity, n_i: u.Quantity, m_i: u.Quantity,
        Z: Union[int, float] = None, to_Hz: bool = False,
        **kwargs) -> u.Quantity:
    """
    Lower-Hybrid resonance frequency (rad/s) --
    [alias for :func:`lower_hybrid_frequency`]
    """
    # add specified keywords to kwargs
    for name, val in zip(('Z', 'to_Hz'), (Z, to_Hz)):
        if val is not None:
            kwargs[name] = val

    return lower_hybrid_frequency(B, m_i, n_i, **kwargs)


@utils.check_quantity({'n_e': {'units': u.cm ** -3,
                               'can_be_negative': False}})
def ope(n_e: u.Quantity, **kwargs) -> u.Quantity:
    """
    electron-plasma frequency (in rad/s)

    .. math::

        \\omega_{pe}^{2} = \\frac{4 \\pi n_{e} e^{2}}{m_e}

    :param n_e: electron number density (in :math:`cm^{-3}`)
    :param kwargs:  supports any keywords used by
        :func:`plasma_frequency`
    """
    return plasma_frequency(n_e, const.e_gauss, const.m_e.cgs,
                            **kwargs['kwargs'])


@utils.check_quantity({'n_i': {'units': u.cm ** -3,
                               'can_be_negative': False},
                       'm_i': {'units': u.g,
                               'can_be_negative': False}})
def opi(n_i: u.Quantity, m_i: u.Quantity,
        Z: Union[int, float] = 1, **kwargs) -> u.Quantity:
    """
    ion-plasma frequency (in rad/s)

    .. math::

        \\omega_{pi}^{2} = \\frac{4 \\pi n_{i} (Z e)^{2}}{m_i}

    :param n_i: ion number density (in :math:`cm^{-3}`)
    :param m_i: ion mass (in g)
    :param Z: ion charge number (:math:`Z=1` DEFAULT)
    :param kwargs:  supports any keywords used by
        :func:`plasma_frequency`
    """
    # condition Z
    if not isinstance(Z, (int, np.integer, float, np.floating)):
        raise TypeError('Z must be of type int or float')
    elif Z <= 0:
        raise PhysicsError(
            'The ion charge number Z must be greater than 0.')

    return plasma_frequency(n_i, Z * const.e_gauss, m_i,
                            **kwargs['kwargs'])


def oUH(B: u.Quantity, n_e: u.Quantity,
        to_Hz: bool = False, **kwargs) -> u.Quantity:
    """
    Upper-Hybrid resonance frequency (rad/s) --
    [alias for :func:`upper_hybrid_frequency`]
    """
    # add specified keywords to kwargs
    for name, val in zip(('to_Hz', ), (to_Hz, )):
        if val is not None:
            kwargs[name] = val

    return upper_hybrid_frequency(B, n_e, **kwargs)


@utils.check_quantity({'n': {'units': u.cm ** -3,
                             "can_be_negative": False},
                       'q': {'units': u.statcoulomb,
                             "can_be_negative": True},
                       'm': {'units': u.g,
                             "can_be_negative": False}})
def plasma_frequency(
        n: u.Quantity, q: u.Quantity, m: u.Quantity,
        to_Hz=False, **kwargs) -> u.Quantity:
    """
    generalized plasma frequency (rad/s)

    .. math::

        \\omega_{p}^{2} = \\frac{4 \\pi n q^{2}}{m}

    :param n: particle number density (in :math:`cm^{-3}`)
    :param q: particle charge (in statcoulombs)
    :param m: particle mass (in g)
    :param to_Hz: :code:`False` (DEFAULT). Set to :code:`True` to
        return frequency in Hz (i.e. divide by :math:`2 * \\pi`)
    """
    # ensure args have correct units
    n = n.to(u.cm ** -3)
    q = q.to(u.Fr)
    m = m.to(u.g)

    # calculate
    _op = np.sqrt((4.0 * const.pi * n.value * (q.value * q.value))
                  / m.value)
    if to_Hz:
        _op = (_op / (2.0 * const.pi)) * u.Hz
    else:
        _op = _op * (u.rad / u.s)
    return _op


@utils.check_quantity({'B': {'units': u.gauss,
                             'can_be_negative': False},
                       'n_e': {'units': u.cm ** -3,
                               'can_be_negative': False}})
def upper_hybrid_frequency(B: u.Quantity, n_e: u.Quantity,
                           to_Hz=False, **kwargs) -> u.Quantity:
    """
    Upper-Hybrid resonance frequency (rad/s)

    .. math::

        \\omega_{UH}^{2} =\\omega_{pe}^{2} + \\Omega_{ce}^{2}

    :param B: magnetic field (in Gauss)
    :param n_e: electron number density (in :math:`cm^{-3}`)
    :param to_Hz: :code:`False` (DEFAULT). Set to :code:`True` to
        return frequency in Hz (i.e. divide by :math:`2 * \\pi`)
    """
    _oce = oce(B, to_Hz=to_Hz, **kwargs)
    _ope = ope(n_e, to_Hz=to_Hz, **kwargs)
    _ouh = np.sqrt((_ope ** 2) + (_oce ** 2))
    return _ouh


# ---- Lengths                                                      ----
@utils.check_quantity({'kTe': {'units': u.eV,
                               'can_be_negative': False},
                       'n': {'units': u.cm ** -3,
                             'can_be_negative': False}})
def Debye_length(kTe: u.Quantity, n: u.Quantity,
                 **kwargs) -> u.Quantity:
    """
    Debye length (in cm)

    .. math::

        \\lambda_{D} = \\sqrt{\\frac{k_{B} T_{e}}{4 \\pi n e^{2}}}

    :param kTe: electron temperature (in eV)
    :param n: number density (in :math:`cm^{-3}`)
    """
    # ensure args have correct units
    kTe = kTe.to(u.erg)
    n = n.to(u.cm ** -3)

    # calculate
    _lD = np.sqrt(kTe / (4.0 * const.pi * n * (const.e_gauss ** 2)))
    return _lD.cgs


@utils.check_quantity({'n': {'units': u.cm ** -3,
                             'can_be_negative': False},
                       'q': {'units': u.statcoulomb,
                             'can_be_negative': True},
                       'm': {'units': u.g,
                             'can_be_negative': False}})
def inertial_length(n: u.Quantity, q: u.Quantity, m: u.Quantity,
                    **kwargs) -> u.Quantity:
    """
    generalized inertial length (cm)

    .. math::

        l =\\frac{c}{\\omega_{p}}

    :param n: particle number density (in :math:`cm^{-3}`)
    :param q: particle charge (in statcoulomb)
    :param m: particle mass (in g)
    """
    _op = plasma_frequency(n, q, m, **kwargs)
    _l = (const.c.cgs.value / _op.value) * u.cm
    return _l


def lD(kTe: u.Quantity, n: u.Quantity, **kwargs) -> u.Quantity:
    """
    Debye length (in cm) -- [alias for :func:`Debye_length`]
    """
    return Debye_length(kTe, n, **kwargs)


@utils.check_quantity({'n_e': {'units': u.cm ** -3,
                               'can_be_negative': False}})
def lpe(n_e: u.Quantity, **kwargs) -> u.Quantity:
    """
    electron-inertial length (cm)

    .. math::

        l_{pe} =\\frac{c}{\\omega_{pe}}

    :param n_e: electron number density (in :math:`cm^{-3}`)
    """
    return inertial_length(n_e, -const.e_gauss, const.m_e, **kwargs)


@utils.check_quantity({'n_i': {'units': u.cm ** -3,
                               'can_be_negative': False},
                       'm_i': {'units': u.g,
                               'can_be_negative': False}})
def lpi(n_i: u.Quantity, m_i: u.Quantity,
        Z: Union[int, float] = 1, **kwargs) -> u.Quantity:
    """
    ion-inertial length (cm)

    .. math::

        l_{pi} =\\frac{c}{\\omega_{pi}}

    :param n_i: ion number density (in :math:`cm^{-3}`)
    :param Z: charge number
    :param m_i: ion mass (in g)
    """
    # condition Z
    if not isinstance(Z, (int, np.integer, float, np.floating)):
        raise TypeError('Z must be of type int or float')
    elif Z <= 0:
        raise PhysicsError(
            'The ion charge number Z must be greater than 0.')

    return inertial_length(n_i, Z * const.e_gauss, m_i, **kwargs)


# ---- Velocities                                                   ----
#@utils.check_relativistic
@utils.check_quantity({'B': {'units': u.gauss,
                             'can_be_negative': False},
                       'n_e': {'units': u.cm ** -3,
                               'can_be_negative': False},
                       'm_i': {'units': u.g,
                               'can_be_negative': False}})
def Alfven_speed(B: u.Quantity, n_e: u.Quantity, m_i: u.Quantity,
                 Z: Union[int, float] = 1, **kwargs) -> u.Quantity:
    """
    Alfvén speed (in cm/s)

    .. math::

        V_{A} &= \\frac{B}
                 {\\sqrt{4 \\pi (n_{i} m_{i} + n_{e} m_{e})}} \\

              &= \\frac{B}{\\sqrt{4 \\pi n_{e} (\\frac{1}{Z}m_{i} + m_{e})}}

    :param B: magnetic field (in Gauss)
    :param n_e: electron number density (in :math:`cm^{3}`)
    :param m_i: ion mass (in g)
    :param Z: ion charge number (:math:`Z=1` DEFAULT)
    """
    # condition Z
    if not isinstance(Z, (int, np.integer, float, np.floating)):
        raise TypeError('Z must be of type int or float')
    elif Z <= 0:
        raise PhysicsError(
            'The ion charge number Z must be greater than 0.')

    # ensure correct units
    B = B.to(u.gauss)
    n_e = n_e.to(u.cm ** -3)
    m_i = m_i.to(u.g)

    # calculated
    _va = B / np.sqrt(4.0 * const.pi * n_e * ((m_i / Z)
                                              + const.m_e.cgs))
    return _va.value * (u.cm / u.s)


def cs(kTe: u.Quantity, m_i: u.Quantity,
       kTi: u.Quantity = None,
       gamma_e: Union[int, float] = None,
       gamma_i: Union[int, float] = None,
       Z: Union[int, float] = None, **kwargs) -> u.Quantity:
    """
    ion-sound speed (cm/s) -- [alias for :func:`ion_sound_speed`
    """
    # add specified keywords to kwargs
    for name, val in zip(('kTi', 'gamma_e', 'gamma_i', 'Z'),
                         (kTi, gamma_e, gamma_i, Z)):
        if val is not None:
            kwargs[name] = val

    return ion_sound_speed(kTe, m_i, **kwargs)


@utils.check_relativistic
@utils.check_quantity({'kTe': {'units': u.eV,
                               'can_be_negative': False},
                       'kTi': {'units': u.eV,
                               'can_be_negative': False},
                       'm_i': {'units': u.g,
                               'can_be_negative': False}})
def ion_sound_speed(kTe: u.Quantity, m_i: u.Quantity,
                    kTi: u.Quantity = (0.0 * u.eV),
                    gamma_e: Union[int, float] = 1,
                    gamma_i: Union[int, float] = 3,
                    Z: Union[int, float] = 1, **kwargs) -> u.Quantity:
    """
    ion sound speed (cm/s)

    .. math::

        c_{s}^{2} = \\frac{\\gamma_{e} Z k_{B} T_{e}
                           + \\gamma_i k_{B} T_{i}}{m_{i}}

    :param kTe: electron temperature (in eV)
    :param kTi: ion temperature (in eV)
    :param m_i: ion mass (in g)
    :param gamma_e: adiabatic index for electrons
        (:math:`\\gamma_e=3` DEFAULT)
    :param gamma_i: adiabatic index for ions
        (:math:`\\gamma_i=3` DEFAULT)
    :param Z: ion charge number (:math:`Z=1` DEFAULT)
    """
    # condition keywords
    for name, val in zip(('gamma_i', 'gamma_e', 'Z'),
                         (gamma_i, gamma_e, Z)):
        if not isinstance(val, (int, np.integer, float, np.floating)):
            raise TypeError(name + ' must be of type int or float')
        elif name == 'Z' and val <= 0:
            raise PhysicsError(
                'The ion charge number Z must be greater than 0.')
        elif val < 1:
            raise PhysicsError('The adiabatic index ' + name
                               + ' must be greater than or equal to 1.')

    # convert temperature to required units
    kTe = kTe.to(u.erg)
    kTi = kTi.to(u.erg)
    m_i = m_i.cgs

    # calculate
    _cs = gamma_e * Z * kTe
    if kTi != 0:
        _cs += gamma_i * kTi
    _cs = np.sqrt(_cs / m_i).to(u.cm / u.s)
    return _cs


def VA(B: u.Quantity, n_e: u.Quantity, m_i: u.Quantity,
       Z: Union[int, float] = None, **kwargs) -> u.Quantity:
    """
    Alfvén speed (in cm/s) -- [alias for :func:`Alfven_speed`]
    """
    # add specified keywords to kwargs
    for name, val in zip(('Z',), (Z,)):
        if val is not None:
            kwargs[name] = val

    return Alfven_speed(B, n_e, m_i, **kwargs)
