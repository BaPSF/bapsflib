#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
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
import astropy.units as u
import numpy as np

from .. import constants as const


def portnum_to_z(portnum):
    """
    Converts LaPD port number to axial z location.

    .. note::

        Port 53 defines z = 0 cm and is the most Northern port.  The +z
        axis points South towards the main cathode.
    """
    return const.port_spacing * (const.ref_port - portnum)


def z_to_portnum(z, unit='cm', rount_to_nearest=False):
    """
    Converts LaPD axial z location to port number.

    Port 53 defines z = 0 cm and is the most Northern port.  The +z
    axis points south towards the main cathode.

    :param z: axial z location
    :param unit: string or :class:`astropy.units` specifying unit type
    """
    # TODO: add functionality to round to nearest port number
    if not isinstance(z, u.Quantity):
        z =u.Quantity(z, unit=unit)

    return const.ref_port - (z / const.port_spacing)
