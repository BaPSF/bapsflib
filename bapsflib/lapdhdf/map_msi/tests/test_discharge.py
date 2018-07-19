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
from ..discharge import hdfMap_msi_discharge
from .common import MSIDiagnosticTestCase

from bapsflib.lapdhdf.tests import FauxHDFBuilder

import numpy as np
import unittest as ut


class TestDischarge(MSIDiagnosticTestCase):
    """Test class for hdfMap_msi_discharge"""

    def setUp(self):
        self.f = FauxHDFBuilder(
            add_modules={'Discharge': {}}
        )
        self.mod = self.f.modules['Discharge']

    def tearDown(self):
        self.f.cleanup()

    @property
    def map(self):
        """Map object of diagnostic"""
        return self.map_diagnostic(self.dgroup)

    @property
    def dgroup(self):
        """Diagnostic group"""
        return self.f['MSI/Discharge']

    @staticmethod
    def map_diagnostic(group):
        """Mapping function"""
        return hdfMap_msi_discharge(group)

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
        #   ~ 'Discharge summary'
        #   ~ 'Cathode-anode voltage'
        #   ~ 'Discharge current'
        # - removed 'Discharge summary' from faux HDF file
        #
        del self.mod['Discharge summary']
        with self.assertWarns(UserWarning):
            self.assertFalse(self.map.build_successful)
        self.mod.knobs.reset()

        # 'Discharge summary' does NOT match expected format        ----
        #
        # 'Discharge summary' is missing a required field
        data = self.mod['Discharge summary'][:]
        fields = list(data.dtype.names)
        fields.remove('Pulse length')
        del self.mod['Discharge summary']
        self.mod.create_dataset('Discharge summary', data=data[fields])
        with self.assertWarns(UserWarning):
            self.assertFalse(self.map.build_successful)
        self.mod.knobs.reset()

        # 'Discharge summary' is not a structured numpy array
        data = np.empty((2, 100), dtype=np.float64)
        del self.mod['Discharge summary']
        self.mod.create_dataset('Discharge summary', data=data)
        with self.assertWarns(UserWarning):
            self.assertFalse(self.map.build_successful)
        self.mod.knobs.reset()

        # 'Cathode-anode voltage' does NOT match expected format    ----
        #
        # dataset has fields
        data = np.empty((2,), dtype=np.dtype([('field1', np.float64),
                                              ('field2', np.float64)]))
        del self.mod['Cathode-anode voltage']
        self.mod.create_dataset('Cathode-anode voltage', data=data)
        with self.assertWarns(UserWarning):
            self.assertFalse(self.map.build_successful)
        self.mod.knobs.reset()

        # shape is not 2 dimensional
        data = np.empty((2, 5, 100), dtype=np.float64)
        del self.mod['Cathode-anode voltage']
        self.mod.create_dataset('Cathode-anode voltage', data=data)
        with self.assertWarns(UserWarning):
            self.assertFalse(self.map.build_successful)
        self.mod.knobs.reset()

        # number of rows is NOT consistent with 'Discharge summary'
        dtype = self.mod['Cathode-anode voltage'].dtype
        shape = (self.mod['Cathode-anode voltage'].shape[0] + 1,
                 self.mod['Cathode-anode voltage'].shape[1])
        data = np.empty(shape, dtype=dtype)
        del self.mod['Cathode-anode voltage']
        self.mod.create_dataset('Cathode-anode voltage', data=data)
        with self.assertWarns(UserWarning):
            self.assertFalse(self.map.build_successful)
        self.mod.knobs.reset()

        # 'Discharge current' does NOT match expected format        ----
        #
        # dataset has fields
        data = np.empty((2,), dtype=np.dtype([('field1', np.float64),
                                              ('field2', np.float64)]))
        del self.mod['Discharge current']
        self.mod.create_dataset('Discharge current', data=data)
        with self.assertWarns(UserWarning):
            self.assertFalse(self.map.build_successful)
        self.mod.knobs.reset()

        # shape is not 2 dimensional
        data = np.empty((2, 5, 100), dtype=np.float64)
        del self.mod['Discharge current']
        self.mod.create_dataset('Discharge current', data=data)
        with self.assertWarns(UserWarning):
            self.assertFalse(self.map.build_successful)
        self.mod.knobs.reset()

        # number of rows is NOT consistent with 'Discharge summary'
        dtype = self.mod['Discharge current'].dtype
        shape = (self.mod['Discharge current'].shape[0] + 1,
                 self.mod['Discharge current'].shape[1])
        data = np.empty(shape, dtype=dtype)
        del self.mod['Discharge current']
        self.mod.create_dataset('Discharge current', data=data)
        with self.assertWarns(UserWarning):
            self.assertFalse(self.map.build_successful)
        self.mod.knobs.reset()

    def test_configs_general_items(self):
        """
        Test behavior for the general, polymorphic elements of the
        `configs` mapping dictionary.
        """
        # ensure general items are present
        self.assertIn('current conversion factor', self.map.configs)
        self.assertIn('voltage conversion factor', self.map.configs)
        self.assertIn('t0', self.map.configs)
        self.assertIn('dt', self.map.configs)

        # ensure general items have expected values
        self.assertEqual(
            [self.dgroup.attrs['Current conversion factor']],
            self.map.configs['current conversion factor'])
        self.assertEqual(
            [self.dgroup.attrs['Voltage conversion factor']],
            self.map.configs['voltage conversion factor'])
        self.assertEqual(
            [self.dgroup.attrs['Start time']],
            self.map.configs['t0'])
        self.assertEqual(
            [self.dgroup.attrs['Timestep']],
            self.map.configs['dt'])

        # check warning if an item is missing
        # - a warning is thrown, but mapping continues
        # - remove attribute 'Timestep'
        del self.dgroup.attrs['Timestep']
        with self.assertWarns(UserWarning):
            self.assertIn('dt', self.map.configs)
            self.assertEqual(self.map.configs['dt'], [])
        self.mod.knobs.reset()


if __name__ == '__main__':
    ut.main()
