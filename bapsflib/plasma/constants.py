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
"""Useful Physical Constants

Constants are imported from :mod:`astropy.constants.codata2014`.
"""
from astropy.constants.codata2014 import (
    c,
    e, e_gauss, e_emu, e_esu,
    eps0,
    g0,
    k_B,
    m_e, m_n, m_p, u,
    mu0,
)
from numpy import pi


__all__ = ['c',
           'e', 'e_gauss', 'e_emu', 'e_esu',
           'eps0',
           'g0',
           'k_B',
           'm_e', 'm_n', 'm_p', 'u',
           'mu0',
           'pi']

'''
class BaPSFConstant(Constant):
    """BaPSF Constant"""
    default_reference = 'Basic Plasma Facility'
    _registry = {}
    _has_incompatible_units = set()


AMU = BaPSFConstant(**{
    'abbrev': 'AMU',
    'name': 'atomic mass unit',
    'value': const.u.cgs.value,
    'unit': const.u.cgs.unit,
    'uncertainty': (const.u.uncertainty * const.u.unit).cgs,
    'system': 'cgs',
})

C = BaPSFConstant(**{
    'abbrev': 'C',
    'name': 'speed of light in vacuum',
    'value': const.c.cgs.value,
    'unit': const.c.cgs.unit,
    'uncertainty': (const.c.uncertainty * const.c.unit).cgs,
    'system': 'cgs',
})

e = BaPSFConstant(**{
    'abbrev': 'e',
    'name': 'elementary charge',
    'value': const.e.cgs.value,
    'unit': const.e.cgs.unit,
    'uncertainty': (const.e.uncertainty * const.e.unit).cgs,
    'system': 'cgs',
})
'''
