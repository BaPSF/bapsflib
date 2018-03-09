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
from ..interferometerarray import hdfMap_msi_interarr
from .common import MSIDiagnosticTestCase

from bapsflib.lapdhdf.tests import FauxHDFBuilder

import unittest as ut


class TestInterferometerArray(MSIDiagnosticTestCase):
    """Test class for hdfMap_msi_interarr"""

    def setUp(self):
        self.f = FauxHDFBuilder(
            add_modules={'Interferometer array': {}}
        )
        self.mod = self.f.modules['Interferometer array']

    def tearDown(self):
        self.f.cleanup()

    @property
    def map(self):
        return hdfMap_msi_interarr(self.dgroup)

    @property
    def dgroup(self):
        return self.f['MSI/Interferometer array']

    def test_map_basics(self):
        """Test all required basic map features."""
        self.assertMSIDiagMapBasics(self.map, self.dgroup)


if __name__ == '__main__':
    ut.main()
