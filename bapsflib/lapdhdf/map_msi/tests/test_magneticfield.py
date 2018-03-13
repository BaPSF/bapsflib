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
from ..magneticfield import hdfMap_msi_magneticfield
from .common import MSIDiagnosticTestCase

from bapsflib.lapdhdf.tests import FauxHDFBuilder

import unittest as ut


class TestMagneticField(MSIDiagnosticTestCase):
    """Test class for hdfMap_msi_magneticfield"""
    # TODO: ADD A WARN TEST IF BUILD UNSUCCESSFUL

    def setUp(self):
        self.f = FauxHDFBuilder(
            add_modules={'Magnetic field': {}}
        )
        self.mod = self.f.modules['Magnetic field']

    def tearDown(self):
        self.f.cleanup()

    @property
    def map(self):
        return hdfMap_msi_magneticfield(self.dgroup)

    @property
    def dgroup(self):
        return self.f['MSI/Magnetic field']

    def test_map_basics(self):
        """Test all required basic map features."""
        self.assertMSIDiagMapBasics(self.map, self.dgroup)


if __name__ == '__main__':
    ut.main()
