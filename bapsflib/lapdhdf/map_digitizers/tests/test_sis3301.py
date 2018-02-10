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
from ..sis3301 import hdfMap_digi_sis3301
from .common import DigitizerTestCase

from bapsflib.lapdhdf.tests import FauxHDFBuilder

import unittest as ut


class TestSIS3301(DigitizerTestCase):
    """Test class for hdfMap_digi_sis3301"""

    def setUp(self):
        self.f = FauxHDFBuilder(add_modules={'SIS 3301': {}})
        self.controls = self.f.modules['SIS 3301']

    def tearDown(self):
        self.f.cleanup()

    @property
    def map(self):
        return hdfMap_digi_sis3301(self.dgroup)

    @property
    def dgroup(self):
        return self.f['Raw data + config/SIS 3301']

    def test_map_basics(self):
        self.assertDigitizerMapBasics(self.map, self.dgroup)


if __name__ == '__main__':
    ut.main()
