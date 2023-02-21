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
import h5py
import numpy as np
import unittest as ut

from bapsflib._hdf.maps import FauxHDFBuilder
from bapsflib._hdf.maps.digitizers.map_digis import HDFMapDigitizers
from bapsflib._hdf.maps.digitizers.templates import HDFMapDigiTemplate


class TestHDFMapDigitizers(ut.TestCase):
    """Test case for HDFMapDigitizers"""

    f = NotImplemented  # type: FauxHDFBuilder
    DIGI_ROOT = "Raw data + config"
    MAP_CLASS = HDFMapDigitizers

    @classmethod
    def setUpClass(cls):
        # create HDF5 file
        super().setUpClass()
        cls.f = FauxHDFBuilder()

    def tearDown(self):
        super().tearDown()
        self.f.remove_all_modules()

    @classmethod
    def tearDownClass(cls):
        """Cleanup temporary HDF5 file"""
        # cleanup and close HDF5 file
        super().tearDownClass()
        cls.f.cleanup()

    @property
    def group(self) -> h5py.Group:
        """Data group holding digitizer groups."""
        return self.f[self.DIGI_ROOT]

    @property
    def map(self):
        """Map of group holding all digitizers."""
        return self.map_digis(self.group)

    def map_digis(self, group: h5py.Group):
        """Mapping function."""
        return self.MAP_CLASS(group)

    def test_not_h5py_group(self):
        """Test error if object to map is not h5py.Group"""
        with self.assertRaises(TypeError):
            self.map_digis(None)

    def test_digi_scenarios(self):
        """
        Test various scenarios of mappable and non-mappable digitizer
        device groups.
        """
        # -- data group has no digitizer devices                    ----
        _map = self.map
        self.assertBasics(_map)
        self.assertEqual(_map, {})

        # -- data group has all mappable devices                    ----
        self.f.add_module("SIS 3301", {})
        self.f.add_module("SIS crate", {})
        _map = self.map
        self.assertBasics(_map)

        # check all controls were mapped
        self.assertEqual(len(_map), 2)
        self.assertIn("SIS 3301", _map)
        self.assertIn("SIS crate", _map)

        # the data group has mappable and unknown digitizers        ----
        self.f.remove_all_modules()
        self.f.add_module("SIS 3301", {})
        self.f["Raw data + config"].create_group("Not known")
        _map = self.map
        self.assertBasics(_map)

        # check correct diagnostics were mapped
        self.assertEqual(len(_map), 1)
        self.assertIn("SIS 3301", _map)
        self.assertNotIn("Not known", _map)

        # delete unknown group
        del self.f["Raw data + config/Not known"]

        # the data group has a dataset                              ----
        self.f.remove_all_modules()
        self.f.add_module("SIS crate", {})
        data = np.empty((2, 100), dtype=np.float32)
        self.f["Raw data + config"].create_dataset("A dataset", data=data)
        _map = self.map
        self.assertBasics(_map)

        # check correct diagnostics were mapped
        self.assertEqual(len(_map), 1)
        self.assertIn("SIS crate", _map)
        self.assertNotIn("A dataset", _map)

        # delete dataset
        del self.f["Raw data + config/A dataset"]

        # the data group has a mappable digitizer but               ----
        # mapping fails                                             ----
        self.f.remove_all_modules()
        self.f.add_module("SIS 3301", {})
        self.f.add_module("SIS crate", {})

        # remove a dataset from 'SIS 3301'
        # - this will cause mapping of 'Waveform' to fail
        #
        sis_group = self.f["Raw data + config/SIS 3301"]
        for name in sis_group:
            if isinstance(sis_group[name], h5py.Dataset):
                del sis_group[name]

        # check map
        _map = self.map
        self.assertBasics(_map)

        # check correct controls were mapped
        self.assertEqual(len(_map), 1)
        self.assertIn("SIS crate", _map)
        self.assertNotIn("SIS 3301", _map)

    def assertBasics(self, _map: HDFMapDigitizers):
        # mapped object is a dictionary
        self.assertIsInstance(_map, dict)

        # all dict items are a mapping class
        for key, val in _map.items():
            self.assertIsInstance(key, str)
            self.assertIsInstance(val, HDFMapDigiTemplate)

        # look for map attributes
        self.assertTrue(hasattr(_map, "_defined_mapping_classes"))
        self.assertTrue(hasattr(_map, "mappable_devices"))

        # check attribute types
        self.assertIsInstance(_map.mappable_devices, tuple)
        self.assertIsInstance(type(_map).mappable_devices, property)
        self.assertEqual(
            sorted(list(_map.mappable_devices)),
            sorted(list(_map._defined_mapping_classes)),
        )


if __name__ == "__main__":
    ut.main()
