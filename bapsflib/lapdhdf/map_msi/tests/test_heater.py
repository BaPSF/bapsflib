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
from ..heater import hdfMap_msi_heater
from .common import MSIDiagnosticTestCase

from bapsflib.lapdhdf.tests import FauxHDFBuilder

import unittest as ut


class TestHeater(MSIDiagnosticTestCase):
    """Test class for hdfMap_msi_heater"""
    # TODO: ADD A WARN TEST IF BUILD UNSUCCESSFUL

    def setUp(self):
        self.f = FauxHDFBuilder(
            add_modules={'Heater': {}}
        )
        self.mod = self.f.modules['Heater']

    def tearDown(self):
        self.f.cleanup()

    @property
    def map(self):
        return hdfMap_msi_heater(self.dgroup)

    @property
    def dgroup(self):
        return self.f['MSI/Heater']

    def test_map_basics(self):
        """Test all required basic map features."""
        self.assertMSIDiagMapBasics(self.map, self.dgroup)


if __name__ == '__main__':
    ut.main()
