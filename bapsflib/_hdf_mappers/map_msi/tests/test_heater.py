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

from bapsflib.lapd._hdf.tests import FauxHDFBuilder

import numpy as np
import unittest as ut


class TestHeater(MSIDiagnosticTestCase):
    """Test class for hdfMap_msi_heater"""

    def setUp(self):
        self.f = FauxHDFBuilder(
            add_modules={'Heater': {}}
        )
        self.mod = self.f.modules['Heater']

    def tearDown(self):
        self.f.cleanup()

    @property
    def map(self):
        """Map object of diagnostic"""
        return self.map_diagnostic(self.dgroup)

    @property
    def dgroup(self):
        """Diagnostic group"""
        return self.f['MSI/Heater']

    @staticmethod
    def map_diagnostic(group):
        """Mapping function"""
        return hdfMap_msi_heater(group)

    def test_map_basics(self):
        """Test all required basic map features."""
        self.assertMSIDiagMapBasics(self.map, self.dgroup)

    def test_not_h5py_group(self):
        """Test error if object to map is not h5py.Group"""
        with self.assertRaises(TypeError):
            self.map_diagnostic(None)

    def test_map_failures(self):
        """Test conditions that result in unsuccessful mappings."""
        # any failed build must throw a UserWarning
        #
        # not all required datasets are found                       ----
        # - Datasets should be:
        #   ~ 'Heater summary'
        # - removed 'Heater summary' from faux HDF file
        #
        del self.mod['Heater summary']
        with self.assertWarns(UserWarning):
            self.assertFalse(self.map.build_successful)
        self.mod.knobs.reset()

        # 'Heater summary' does NOT match expected format           ----
        #
        # define dataset name
        dset_name = 'Heater summary'

        # 'Heater summary' is missing a required field
        data = self.mod[dset_name][:]
        fields = list(data.dtype.names)
        fields.remove('Heater current')
        del self.mod[dset_name]
        self.mod.create_dataset(dset_name, data=data[fields])
        with self.assertWarns(UserWarning):
            self.assertFalse(self.map.build_successful)
        self.mod.knobs.reset()

        # 'Heater summary' is not a structured numpy array
        data = np.empty((2, 100), dtype=np.float64)
        del self.mod[dset_name]
        self.mod.create_dataset(dset_name, data=data)
        with self.assertWarns(UserWarning):
            self.assertFalse(self.map.build_successful)
        self.mod.knobs.reset()

    def test_configs_general_items(self):
        """
        Test behavior for the general, polymorphic elements of the
        `configs` mapping dictionary.
        """
        # get map instance
        _map = self.map

        # ensure general items are present
        self.assertIn('calib tag', _map.configs)

        # ensure general items have expected values
        self.assertEqual(
            [self.dgroup.attrs['Calibration tag']],
            _map.configs['calib tag'])

        # check warning if an item is missing
        # - a warning is thrown, but mapping continues
        # - remove attribute 'Calibration tag'
        del self.dgroup.attrs['Calibration tag']
        with self.assertWarns(UserWarning):
            _map = self.map
            self.assertIn('calib tag', _map.configs)
            self.assertEqual(_map.configs['calib tag'], [])
        self.mod.knobs.reset()


if __name__ == '__main__':
    ut.main()
