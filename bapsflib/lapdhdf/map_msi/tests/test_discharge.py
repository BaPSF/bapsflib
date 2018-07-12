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
    # TODO: ADD A WARN TEST IF BUILD UNSUCCESSFUL

    def setUp(self):
        self.f = FauxHDFBuilder(
            add_modules={'Discharge': {}}
        )
        self.mod = self.f.modules['Discharge']

    def tearDown(self):
        self.f.cleanup()

    @property
    def map(self):
        return hdfMap_msi_discharge(self.dgroup)

    @property
    def dgroup(self):
        return self.f['MSI/Discharge']

    def test_map_basics(self):
        """Test all required basic map features."""
        self.assertMSIDiagMapBasics(self.map, self.dgroup)

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

        # 'Discharge summary' is not a structured array
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


if __name__ == '__main__':
    ut.main()
