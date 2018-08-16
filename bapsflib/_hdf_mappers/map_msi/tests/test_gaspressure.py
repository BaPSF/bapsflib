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

from bapsflib.lapd._hdf.tests import FauxHDFBuilder

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
        """Map object of diagnostic"""
        return self.map_diagnostic(self.dgroup)

    @property
    def dgroup(self):
        """Diagnostic group"""
        return self.f['MSI/Gas pressure']

    @staticmethod
    def map_diagnostic(group):
        """Mapping function"""
        return hdfMap_msi_gaspressure(group)

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
        # define dataset name
        dset_name = 'Gas pressure summary'

        # 'Gas pressure summary' is missing a required field
        data = self.mod[dset_name][:]
        fields = list(data.dtype.names)
        fields.remove('Fill pressure')
        del self.mod[dset_name]
        self.mod.create_dataset(dset_name, data=data[fields])
        with self.assertWarns(UserWarning):
            self.assertFalse(self.map.build_successful)
        self.mod.knobs.reset()

        # 'Gas pressure summary' is not a structured numpy array
        data = np.empty((2, 100), dtype=np.float64)
        del self.mod[dset_name]
        self.mod.create_dataset(dset_name, data=data)
        with self.assertWarns(UserWarning):
            self.assertFalse(self.map.build_successful)
        self.mod.knobs.reset()

        # 'RGA partial pressures' does NOT match expected format    ----
        #
        # define dataset name
        dset_name = 'RGA partial pressures'

        # dataset has fields
        data = np.empty((2,), dtype=np.dtype([('field1', np.float64),
                                              ('field2', np.float64)]))
        del self.mod[dset_name]
        self.mod.create_dataset(dset_name, data=data)
        with self.assertWarns(UserWarning):
            self.assertFalse(self.map.build_successful)
        self.mod.knobs.reset()

        # shape is not 2 dimensional
        data = np.empty((2, 5, 100), dtype=np.float64)
        del self.mod[dset_name]
        self.mod.create_dataset(dset_name, data=data)
        with self.assertWarns(UserWarning):
            self.assertFalse(self.map.build_successful)
        self.mod.knobs.reset()

        # number of rows is NOT consistent with 'Discharge summary'
        dtype = self.mod[dset_name].dtype
        shape = (self.mod[dset_name].shape[0] + 1,
                 self.mod[dset_name].shape[1])
        data = np.empty(shape, dtype=dtype)
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
        self.assertIn('RGA AMUs', _map.configs)
        self.assertIn('ion gauge calib tag', _map.configs)
        self.assertIn('RGA calib tag', _map.configs)

        # ensure general items have expected values
        self.assertTrue(np.array_equal(
            self.dgroup.attrs['RGA AMUs'],
            _map.configs['RGA AMUs']))
        self.assertEqual(
            [self.dgroup.attrs['Ion gauge calibration tag']],
            _map.configs['ion gauge calib tag'])
        self.assertEqual(
            [self.dgroup.attrs['RGA calibration tag']],
            _map.configs['RGA calib tag'])

        # check warning if an item is missing
        # - a warning is thrown, but mapping continues
        # - remove attribute 'RGA AMUs'
        del self.dgroup.attrs['RGA AMUs']
        with self.assertWarns(UserWarning):
            _map = self.map
            self.assertIn('RGA AMUs', _map.configs)
            self.assertEqual(_map.configs['RGA AMUs'], [])
        self.mod.knobs.reset()


if __name__ == '__main__':
    ut.main()
