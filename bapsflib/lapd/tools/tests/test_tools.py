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
import unittest as ut

import bapsflib.lapd.constants as const

from bapsflib.lapd.tools import portnum_to_z, z_to_portnum


class TestTools(ut.TestCase):
    """Test LaPD tools. (:mod:`bapsflib.lapd.tools.tools`)"""

    def test_portnum_to_z(self):
        # 1st scenario
        portnums = (5, 20)
        for portnum in portnums:
            p2z = portnum_to_z(portnum)
            val = const.port_spacing * (const.ref_port - portnum)
            self.assertIsInstance(p2z, u.Quantity)
            self.assertEqual(p2z.unit, u.cm)
            self.assertEqual(p2z.value, val.value)

    def test_z_to_portnum(self):
        zs = (1051.155, 875.43, 447.3, 1214, u.Quantity(875.43, unit="cm"))
        for z in zs:
            portnum = z_to_portnum(z)
            if not isinstance(z, u.Quantity):
                z = u.Quantity(z, unit="cm")
            val = const.ref_port - (z / const.port_spacing)
            self.assertIsInstance(portnum, u.Quantity)
            self.assertEqual(portnum.unit, u.dimensionless_unscaled)
            self.assertEqual(portnum.value, val.value)

        # use `round_to_nearest=True`
        for z in zs:
            portnum = z_to_portnum(z, round_to_nearest=True)
            if not isinstance(z, u.Quantity):
                z = u.Quantity(z, unit="cm")
            val = const.ref_port - (z / const.port_spacing)
            val = np.round(val).astype(np.int8)
            self.assertIsInstance(portnum, u.Quantity)
            self.assertEqual(portnum.unit, u.dimensionless_unscaled)
            self.assertEqual(portnum.value, val.value)

        # pass a z in not in 'com'
        z = u.Quantity(8.7, unit="m")
        portnum = z_to_portnum(z)
        val = const.ref_port - (z.cgs / const.port_spacing)
        self.assertIsInstance(portnum, u.Quantity)
        self.assertEqual(portnum.unit, u.dimensionless_unscaled)
        self.assertEqual(portnum.value, val.value)


if __name__ == "__main__":
    ut.main()
