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
"""Main sub-module for LaPD tool functionality."""
__all__ = ["portnum_to_z", "z_to_portnum"]

import astropy.units as u
import numpy as np

from typing import Union

from bapsflib.lapd import constants as const


def portnum_to_z(portnum: Union[int, float]) -> u.Quantity:
    """
    Converts LaPD port number to axial z location.

    .. note::

        Port 53 defines z = 0 cm and is the most Northern port.  The +z
        axis points South towards the main cathode.
    """
    val = const.port_spacing * (const.ref_port - portnum)
    return val.cgs


def z_to_portnum(
    z: Union[int, float, u.Quantity], unit="cm", round_to_nearest=False
) -> u.Quantity:
    """
    Converts LaPD axial z location to port number.

    :param z: axial z location
    :param unit: string or :class:`astropy.units` specifying unit type
    :param bool round_to_nearest: :code:`False` (DEFAULT), :code:`True`
        will round the port number to the nearest full integer

    .. note::

        Port 53 defines z = 0 cm and is the most Northern port.  The +z
        axis points South towards the main cathode.
    """
    # convert to float
    if isinstance(z, int):
        z = float(z)

    # convert to astropy.units.Quantity
    if not isinstance(z, u.Quantity):
        z = u.Quantity(z, unit=unit)

    # calc port number
    portnum = const.ref_port - (z.cgs / const.port_spacing)

    # convert to nearest port number
    if round_to_nearest:
        portnum = np.round(portnum).astype(np.int8)

    # return
    return portnum
