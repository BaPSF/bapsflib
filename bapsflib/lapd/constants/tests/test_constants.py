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
import unittest as ut

from astropy.constants import Constant

from bapsflib.lapd.constants import port_spacing, ref_port
from bapsflib.lapd.constants.constants import BaPSFConstant


class TestConstants(ut.TestCase):
    """
    Test LaPD constants. (:mod:`bapsflib.lapd.constants.constants`)
    """

    def test_BaPSFConstant(self):
        self.assertTrue(issubclass(BaPSFConstant, Constant))
        self.assertEqual(BaPSFConstant.default_reference, "Basic Plasma Science Facility")

    def test_port_spacing(self):
        self.assertIsInstance(port_spacing, BaPSFConstant)
        self.assertEqual(port_spacing.value, 31.95)
        self.assertEqual(port_spacing.unit, u.cm)
        self.assertEqual(port_spacing.uncertainty, 1.0)

    def test_ref_port(self):
        self.assertIsInstance(ref_port, BaPSFConstant)
        self.assertEqual(ref_port.value, 53)
        self.assertEqual(ref_port.unit, u.dimensionless_unscaled)


if __name__ == "__main__":
    ut.main()
