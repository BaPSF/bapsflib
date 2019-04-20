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
    e, e_gauss,
    eps0,
    g0,
    k_B,
    m_e, m_n, m_p, u,
    mu0,
)
from bapsflib.utils import BaPSFConstant
from numpy import pi


__all__ = ['c',
           'e', 'e_gauss',
           'eps0',
           'g0',
           'k_B',
           'm_e', 'm_n', 'm_p', 'u',
           'mu0',
           'pi']

# rename some attributes for clarity
e = BaPSFConstant(**{
    'abbrev': 'e',
    'name': 'Elementary charge',
    'value': e.value,
    'unit': e.unit.name,
    'uncertainty': e.uncertainty,
    'system': e.system,
})
e_gauss = BaPSFConstant(**{
    'abbrev': 'e_gauss',
    'name': 'Elementary charge',
    'value': e_gauss.value,
    'unit': e_gauss.unit.name,
    'uncertainty': e_gauss.uncertainty,
    'system': e_gauss.system,
})
u = BaPSFConstant(**{
    'abbrev': 'u',
    'name': 'Atomic mass unit',
    'value': u.value,
    'unit': u.unit.name,
    'uncertainty': u.uncertainty,
    'system': u.system,
})

# clean up
del BaPSFConstant

# The following code is modified from astropy.constants to produce a
# table containing information on the constants.

# initialize table
_tb_div = ((8 * '=') + ' '
           + (17 * '=') + ' '
           + (10 * '=') + ' '
           + (7 * '=') + ' '
           + (44 * '='))
_lines = [
    'The following constants are available:\n',
    _tb_div,
    '{0:^8} {1:^17} {2:^10} {3:^7} {4}'.format('Name', 'Value', 'Units',
                                              'System', 'Description'),
    _tb_div,
    '{0:^8} {1:^17.12f} {2:^10} {3:^7} {4}'.format(
        'pi', pi, '', '',
        'Ratio of circumference to diameter of circle'),
]

# add lines to table
_constants = [eval(item) for item in dir() if item[0] != '_' and item != 'pi']
_const = None
for _const in _constants:
    _lines.append('{0:^8} {1:^17.12g} {2:^10} {3:^7} {4}'
                  .format(_const.abbrev, _const.value,
                          _const._unit_string, _const.system,
                          _const.name))

_lines.append(_lines[1])

# add table to docstrings
__doc__ += '\n'
__doc__ += '\n'.join(_lines)

# remove clutter from namespace
del _const, _constants, _lines, _tb_div,
