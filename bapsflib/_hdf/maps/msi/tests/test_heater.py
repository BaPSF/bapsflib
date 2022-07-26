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

from bapsflib._hdf.maps.msi.heater import HDFMapMSIHeater
from bapsflib._hdf.maps.msi.tests.common import MSIDiagnosticTestCase
from bapsflib.utils.exceptions import HDFMappingError


class TestHeater(MSIDiagnosticTestCase):
    """Test class for HDFMapMSIHeater"""

    DEVICE_NAME = "Heater"
    DEVICE_PATH = "/MSI/Heater"
    MAP_CLASS = HDFMapMSIHeater

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
        #   ~ 'Heater summary'
        # - removed 'Heater summary' from faux HDF file
        #
        del self.mod["Heater summary"]
        with self.assertRaises(HDFMappingError):
            _map = self.map
        self.mod.knobs.reset()

        # 'Heater summary' does NOT match expected format           ----
        #
        # define dataset name
        dset_name = "Heater summary"

        # 'Heater summary' is missing a required field
        data = self.mod[dset_name][:]
        fields = list(data.dtype.names)
        fields.remove("Heater current")
        del self.mod[dset_name]
        self.mod.create_dataset(dset_name, data=data[fields])
        with self.assertRaises(HDFMappingError):
            _map = self.map
        self.mod.knobs.reset()

        # 'Heater summary' is not a structured numpy array
        data = np.empty((2, 100), dtype=np.float64)
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

        # ensure general items have expected values
        self.assertEqual(
            [self.dgroup.attrs["Calibration tag"]], _map.configs["calib tag"]
        )

        # check warning if an item is missing
        # - a warning is thrown, but mapping continues
        # - remove attribute 'Calibration tag'
        del self.dgroup.attrs["Calibration tag"]
        with self.assertWarns(UserWarning):
            _map = self.map
            self.assertIn("calib tag", _map.configs)
            self.assertEqual(_map.configs["calib tag"], [])
        self.mod.knobs.reset()


if __name__ == "__main__":
    ut.main()
