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
import numpy as np
import unittest as ut

from bapsflib._hdf.maps.msi.discharge import HDFMapMSIDischarge
from bapsflib._hdf.maps.msi.tests.common import MSIDiagnosticTestCase
from bapsflib.utils.exceptions import HDFMappingError


class TestDischarge(MSIDiagnosticTestCase):
    """Test class for HDFMapMSIDischarge"""

    # define setup variables
    DEVICE_NAME = "Discharge"
    DEVICE_PATH = "/MSI/Discharge"
    MAP_CLASS = HDFMapMSIDischarge

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

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
        del self.mod["Discharge summary"]
        with self.assertRaises(HDFMappingError):
            _map = self.map
        self.mod.knobs.reset()

        # 'Discharge summary' does NOT match expected format        ----
        #
        # define dataset name
        dset_name = "Discharge summary"

        # 'Discharge summary' is missing a required field
        data = self.mod[dset_name][:]
        fields = list(data.dtype.names)
        fields.remove("Pulse length")
        del self.mod[dset_name]
        self.mod.create_dataset(dset_name, data=data[fields])
        with self.assertRaises(HDFMappingError):
            _map = self.map
        self.mod.knobs.reset()

        # 'Discharge summary' is not a structured numpy array
        data = np.empty((2, 100), dtype=np.float64)
        del self.mod[dset_name]
        self.mod.create_dataset(dset_name, data=data)
        with self.assertRaises(HDFMappingError):
            _map = self.map
        self.mod.knobs.reset()

        # 'Cathode-anode voltage' does NOT match expected format    ----
        #
        # define dataset name
        dset_name = "Cathode-anode voltage"

        # dataset has fields
        data = np.empty(
            (2,), dtype=np.dtype([("field1", np.float64), ("field2", np.float64)])
        )
        del self.mod[dset_name]
        self.mod.create_dataset(dset_name, data=data)
        with self.assertRaises(HDFMappingError):
            _map = self.map
        self.mod.knobs.reset()

        # shape is not 2 dimensional
        data = np.empty((2, 5, 100), dtype=np.float64)
        del self.mod[dset_name]
        self.mod.create_dataset(dset_name, data=data)
        with self.assertRaises(HDFMappingError):
            _map = self.map
        self.mod.knobs.reset()

        # number of rows is NOT consistent with 'Discharge summary'
        dtype = self.mod[dset_name].dtype
        shape = (self.mod[dset_name].shape[0] + 1, self.mod[dset_name].shape[1])
        data = np.empty(shape, dtype=dtype)
        del self.mod[dset_name]
        self.mod.create_dataset(dset_name, data=data)
        with self.assertRaises(HDFMappingError):
            _map = self.map
        self.mod.knobs.reset()

        # 'Discharge current' does NOT match expected format        ----
        #
        # define dataset name
        dset_name = "Discharge current"

        # dataset has fields
        data = np.empty(
            (2,), dtype=np.dtype([("field1", np.float64), ("field2", np.float64)])
        )
        del self.mod[dset_name]
        self.mod.create_dataset(dset_name, data=data)
        with self.assertRaises(HDFMappingError):
            _map = self.map
        self.mod.knobs.reset()

        # shape is not 2 dimensional
        data = np.empty((2, 5, 100), dtype=np.float64)
        del self.mod[dset_name]
        self.mod.create_dataset(dset_name, data=data)
        with self.assertRaises(HDFMappingError):
            _map = self.map
        self.mod.knobs.reset()

        # number of rows is NOT consistent with 'Discharge summary'
        dtype = self.mod[dset_name].dtype
        shape = (self.mod[dset_name].shape[0] + 1, self.mod[dset_name].shape[1])
        data = np.empty(shape, dtype=dtype)
        del self.mod[dset_name]
        self.mod.create_dataset(dset_name, data=data)
        with self.assertRaises(HDFMappingError):
            _map = self.map
        self.mod.knobs.reset()

    def test_configs_general_items(self):
        """
        Test behavior for the general, polymorphic elements of the
        `configs` mapping dictionary.
        """
        # get map instance
        _map = self.map

        # ensure general items are present
        self.assertIn("current conversion factor", _map.configs)
        self.assertIn("voltage conversion factor", _map.configs)
        self.assertIn("t0", _map.configs)
        self.assertIn("dt", _map.configs)

        # ensure general items have expected values
        self.assertEqual(
            [self.dgroup.attrs["Current conversion factor"]],
            _map.configs["current conversion factor"],
        )
        self.assertEqual(
            [self.dgroup.attrs["Voltage conversion factor"]],
            _map.configs["voltage conversion factor"],
        )
        self.assertEqual([self.dgroup.attrs["Start time"]], _map.configs["t0"])
        self.assertEqual([self.dgroup.attrs["Timestep"]], _map.configs["dt"])

        # check warning if an item is missing
        # - a warning is thrown, but mapping continues
        # - remove attribute 'Timestep'
        del self.dgroup.attrs["Timestep"]
        with self.assertWarns(UserWarning):
            _map = self.map
            self.assertIn("dt", _map.configs)
            self.assertEqual(_map.configs["dt"], [])
        self.mod.knobs.reset()


if __name__ == "__main__":
    ut.main()
