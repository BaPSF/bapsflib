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
from plasmapy import utils
from typing import Union


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
    particle cyclotron frequency (rad/s)

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
                           m_i: u.Quantity, Z: Union[int, float],
                           to_Hz=False, **kwargs) -> u.Quantity:
    """
    Lower-Hybrid Resonance Frequency (rad/s)

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
    :param Z: ion charge number
    :param to_Hz: :code:`False` (DEFAULT). Set to :code:`True` to
        return frequency in Hz (i.e. divide by :math:`2 * \\pi`)
    """
    _oci = oci(Z, B, m_i, to_Hz=to_Hz, **kwargs)
    _opi = opi(n_i, Z, m_i, to_Hz=to_Hz, **kwargs)
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
    return cyclotron_frequency(-const.e_gauss, B, const.m_e,
                               **kwargs['kwargs'])


@utils.check_quantity({'B': {'units': u.Gauss,
                             "can_be_negative": False},
                       'm_i': {'units': u.g,
                               "can_be_negative": False}})
def oci(Z: Union[int, float], B: u.Quantity, m_i: u.Quantity,
        **kwargs) -> u.Quantity:
    """
    ion-cyclotron frequency (rad/s)

    .. math::

        \\Omega_{ci} = \\frac{Z |e| B}{m_{i} c}

    :param Z: charge number
    :param B: magnetic-field (in Gauss)
    :param m_i: ion mass (in grams)
    :param kwargs: supports any keywords used by
        :func:`cyclotron_frequency`
    """
    return cyclotron_frequency(Z * const.e_gauss, B, m_i,
                               **kwargs['kwargs'])


def oLH(B: u.Quantity, n_i: u.Quantity,
        m_i: u.Quantity, Z: Union[int, float],
        to_Hz=False, **kwargs) -> u.Quantity:
    """
    Lower-Hybrid Resonance Frequency (rad/s)

    [alias for :func:`lower_hybrid_frequency`]
    """
    return lower_hybrid_frequency(B, m_i, n_i, Z, to_Hz=to_Hz, **kwargs)


@utils.check_quantity({'n_e': {'units': u.cm ** -3,
                               'can_be_negative': False}})
def ope(n_e: u.Quantity, **kwargs) -> u.Quantity:
    """
    electron-plasma frequency (in rad/s)

    .. math::

        \\omega_{pe}^{2} = \\frac{4 \\pi n_{e} e^{2}}{m_e}

    :param n_e: electron number density (in :math:`cm^{-3}`)
    :param kwargs:  supports any keywords used by
        :func:`plasma_frequency_generic`
    """
    return plasma_frequency_generic(n_e, const.e_gauss, const.m_e,
                                    **kwargs['kwargs'])


@utils.check_quantity({'n_i': {'units': u.cm ** -3,
                               'can_be_negative': False},
                       'm_i': {'units': u.g,
                               'can_be_negative': False}})
def opi(n_i: u.Quantity, Z: Union[int, float], m_i: u.Quantity,
        **kwargs) -> u.Quantity:
    """
    ion-plasma frequency (in rad/s)

    .. math::

        \\omega_{pi}^{2} = \\frac{4 \\pi n_{i} (Z e)^{2}}{m_i}

    :param n_i: ion number density (in :math:`cm^{-3}`)
    :param Z: charge number
    :param m_i: ion mass (in g)
    :param kwargs:  supports any keywords used by
        :func:`plasma_frequency_generic`
    """
    return plasma_frequency_generic(n_i, Z * const.e_gauss, m_i,
                                    **kwargs['kwargs'])


def oUH(B: u.Quantity, n_e: u.Quantity,
        to_Hz=False, **kwargs) -> u.Quantity:
    """
    Upper-Hybrid Resonance Frequency (rad/s)

    [alias for :func:`upper_hybrid_frequency`]
    """
    return upper_hybrid_frequency(B, n_e, to_Hz=to_Hz, **kwargs)


@utils.check_quantity({'n': {'units': u.cm ** -3,
                             "can_be_negative": False},
                       'q': {'units': u.statcoulomb,
                             "can_be_negative": True},
                       'm': {'units': u.g,
                             "can_be_negative": False}})
def plasma_frequency_generic(
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
    Upper-Hybrid Resonance frequency (rad/s)

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
