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
"""
:mod:`bapsflib` defined equivalencies for :mod:`astropy.units`
"""

__all__ = ['temperature_and_energy']

import astropy.units as u

from typing import (List, Tuple)


def temperature_and_energy():
    """
    Convert between Kelvin, Celsius, Fahrenheit, and eV.  (An
    :mod:`astropy.units.equivalencies`)
    """
    # combine standard temperature and energy equivalencies
    equiv = u.temperature()  # type: List[Tuple]
    equiv.extend(u.temperature_energy())

    # construct functions for non-Kelvin to energy (and visa-versa)
    # conversions
    def convert_C_to_eV(x):
        # convert Celsius to eV
        x = (x * u.deg_C).to(u.K, equivalencies=equiv)
        return x.to_value(u.eV, equivalencies=equiv)

    def convert_eV_to_C(x):
        # convert eV to Celsius
        x = (x * u.eV).to(u.K, equivalencies=equiv)
        return x.to_value(u.deg_C, equivalencies=equiv)

    def convert_F_to_eV(x):
        # convert Fahrenheit to eV
        x = (x * u.imperial.deg_F).to(u.K, equivalencies=equiv)
        return x.to_value(u.eV, equivalencies=equiv)

    def convert_eV_to_F(x):
        # convert eV to Fahrenheit to eV
        x = (x * u.eV).to(u.K, equivalencies=equiv)
        return x.to_value(u.imperial.deg_F, equivalencies=equiv)

    # add new equivalencies to the complete list
    equiv.append((u.deg_C, u.eV, convert_C_to_eV, convert_eV_to_C))
    equiv.append((u.imperial.deg_F, u.eV,
                  convert_F_to_eV, convert_eV_to_F))
    return equiv
