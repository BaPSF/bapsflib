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

from bapsflib._hdf.maps.msi.magneticfield import HDFMapMSIMagneticField
from bapsflib._hdf.maps.msi.tests.common import MSIDiagnosticTestCase
from bapsflib.utils.exceptions import HDFMappingError


class TestMagneticField(MSIDiagnosticTestCase):
    """Test class for HDFMapMSIMagneticField"""

    # define setup variables
    DEVICE_NAME = "Magnetic field"
    DEVICE_PATH = "/MSI/Magnetic field"
    MAP_CLASS = HDFMapMSIMagneticField

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test_map_failures(self):
        """Test conditions that result in unsuccessful mappings."""
        # any failed build must throw a HDFMappingError
        #
        # not all required datasets are found                   ----
        # - Datasets should be:
        #   ~ 'Magnetic field summary'
        #   ~ 'Magnetic field profile'
        #   ~ 'Magnetic power supply currents'
        # - removed 'Discharge summary' from faux HDF file
        #
        del self.mod["Magnetic field summary"]
        with self.assertRaises(HDFMappingError):
            _map = self.map
        self.mod.knobs.reset()

        # 'Magnetic field summary' does NOT match expected format   ----
        #
        # define dataset name
        dset_name = "Magnetic field summary"

        # 'Magnetic field summary' is missing a required field
        data = self.mod[dset_name][:]
        fields = list(data.dtype.names)
        fields.remove("Peak magnetic field")
        del self.mod[dset_name]
        self.mod.create_dataset(dset_name, data=data[fields])
        with self.assertRaises(HDFMappingError):
            _map = self.map
        self.mod.knobs.reset()

        # 'Magnetic field summary' is not a structured numpy array
        data = np.empty((2, 100), dtype=np.float64)
        del self.mod[dset_name]
        self.mod.create_dataset(dset_name, data=data)
        with self.assertRaises(HDFMappingError):
            _map = self.map
        self.mod.knobs.reset()

        # 'Magnetic field profile' does NOT match expected format   ----
        #
        # define dataset name
        dset_name = "Magnetic field profile"

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

        # number of rows is NOT consistent with 'Magnetic field summary'
        dtype = self.mod[dset_name].dtype
        shape = (self.mod[dset_name].shape[0] + 1, self.mod[dset_name].shape[1])
        data = np.empty(shape, dtype=dtype)
        del self.mod[dset_name]
        self.mod.create_dataset(dset_name, data=data)
        with self.assertRaises(HDFMappingError):
            _map = self.map
        self.mod.knobs.reset()

        # 'Magnet power supply currents' does NOT match             ----
        # expected format                                           ----
        #
        # define dataset name
        dset_name = "Magnet power supply currents"

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

        # number of rows is NOT consistent with 'Magnetic field summary'
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
        self.assertIn("calib tag", _map.configs)
        self.assertIn("z", _map.configs)

        # ensure general items have expected values
        self.assertEqual(
            [self.dgroup.attrs["Calibration tag"]], _map.configs["calib tag"]
        )
        self.assertTrue(
            np.array_equal(self.dgroup.attrs["Profile z locations"], _map.configs["z"])
        )

        # check warning if an item is missing
        # - a warning is thrown, but mapping continues
        # - remove attribute 'Profile z locations'
        del self.dgroup.attrs["Profile z locations"]
        with self.assertWarns(UserWarning):
            _map = self.map
            self.assertIn("z", _map.configs)
            self.assertEqual(_map.configs["z"], [])
        self.mod.knobs.reset()


if __name__ == "__main__":
    ut.main()
