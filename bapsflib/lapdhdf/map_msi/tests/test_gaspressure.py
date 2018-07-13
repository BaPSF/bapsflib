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
from ..gaspressure import hdfMap_msi_gaspressure
from .common import MSIDiagnosticTestCase

from bapsflib.lapdhdf.tests import FauxHDFBuilder

import numpy as np
import unittest as ut


class TestGasPressure(MSIDiagnosticTestCase):
    """Test class for hdfMap_msi_gaspressure"""

    def setUp(self):
        self.f = FauxHDFBuilder(
            add_modules={'Gas pressure': {}}
        )
        self.mod = self.f.modules['Gas pressure']

    def tearDown(self):
        self.f.cleanup()

    @property
    def map(self):
        return hdfMap_msi_gaspressure(self.dgroup)

    @property
    def dgroup(self):
        return self.f['MSI/Gas pressure']

    def test_map_basics(self):
        """Test all required basic map features."""
        self.assertMSIDiagMapBasics(self.map, self.dgroup)

    def test_map_failures(self):
        """Test conditions that result in unsuccessful mappings."""
        # any failed build must throw a UserWarning
        #
        # not all required datasets are found                       ----
        # - Datasets should be:
        #   ~ 'Gas pressure summary'
        #   ~ 'RGA partial pressures'
        # - removed 'Gas pressure summary' from faux HDF file
        #
        del self.mod['Gas pressure summary']
        with self.assertWarns(UserWarning):
            self.assertFalse(self.map.build_successful)
        self.mod.knobs.reset()

        # 'Gas pressure summary' does NOT match expected format     ----
        #
        # 'Gas pressure summary' is missing a required field
        data = self.mod['Gas pressure summary'][:]
        fields = list(data.dtype.names)
        fields.remove('Fill pressure')
        del self.mod['Gas pressure summary']
        self.mod.create_dataset('Gas pressure summary', data=data[fields])
        with self.assertWarns(UserWarning):
            self.assertFalse(self.map.build_successful)
        self.mod.knobs.reset()

        # 'Gas pressure summary' is not a structured numpy array
        data = np.empty((2, 100), dtype=np.float64)
        del self.mod['Gas pressure summary']
        self.mod.create_dataset('Gas pressure summary', data=data)
        with self.assertWarns(UserWarning):
            self.assertFalse(self.map.build_successful)
        self.mod.knobs.reset()

        # 'RGA partial pressures' does NOT match expected format    ----
        #
        # dataset has fields
        data = np.empty((2,), dtype=np.dtype([('field1', np.float64),
                                              ('field2', np.float64)]))
        del self.mod['RGA partial pressures']
        self.mod.create_dataset('RGA partial pressures', data=data)
        with self.assertWarns(UserWarning):
            self.assertFalse(self.map.build_successful)
        self.mod.knobs.reset()

        # shape is not 2 dimensional
        data = np.empty((2, 5, 100), dtype=np.float64)
        del self.mod['RGA partial pressures']
        self.mod.create_dataset('RGA partial pressures', data=data)
        with self.assertWarns(UserWarning):
            self.assertFalse(self.map.build_successful)
        self.mod.knobs.reset()

        # number of rows is NOT consistent with 'Discharge summary'
        dtype = self.mod['RGA partial pressures'].dtype
        shape = (self.mod['RGA partial pressures'].shape[0] + 1,
                 self.mod['RGA partial pressures'].shape[1])
        data = np.empty(shape, dtype=dtype)
        del self.mod['RGA partial pressures']
        self.mod.create_dataset('RGA partial pressures', data=data)
        with self.assertWarns(UserWarning):
            self.assertFalse(self.map.build_successful)
        self.mod.knobs.reset()

    def test_configs_general_items(self):
        """
        Test behavior for the general, polymorphic elements of the
        `configs` mapping dictionary.
        """
        # ensure general items are present
        self.assertIn('RGA AMUs', self.map.configs)
        self.assertIn('ion gauge calib tag', self.map.configs)
        self.assertIn('RGA calib tag', self.map.configs)

        # ensure general items have expected values
        self.assertTrue(np.array_equal(
            [self.dgroup.attrs['RGA AMUs']],
            self.map.configs['RGA AMUs']))
        self.assertEqual(
            [self.dgroup.attrs['Ion gauge calibration tag']],
            self.map.configs['ion gauge calib tag'])
        self.assertEqual(
            [self.dgroup.attrs['RGA calibration tag']],
            self.map.configs['RGA calib tag'])

        # check warning if an item is missing
        # - a warning is thrown, but mapping continues
        # - remove attribute 'RGA AMUs'
        del self.dgroup.attrs['RGA AMUs']
        with self.assertWarns(UserWarning):
            self.assertIn('RGA AMUs', self.map.configs)
            self.assertEqual(self.map.configs['RGA AMUs'], [])
        self.mod.knobs.reset()


if __name__ == '__main__':
    ut.main()
