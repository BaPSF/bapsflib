#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is part of the bapsflib package, a Python toolkit for the
# BaPSF group at UCLA.
#
# http://plasma.physics.ucla.edu/
#
# Copyright 2017-2019 Erik T. Everson and contributors
#
# License: Standard 3-clause BSD; see "LICENSES/LICENSE.txt" for full
#   license terms and contributor agreement.
#
import h5py
import unittest as ut

from bapsflib._hdf.maps.controls import ConType
from bapsflib._hdf.maps.controls.nixz import HDFMapControlNIXZ
from bapsflib._hdf.maps.controls.tests.common import ControlTestCase
from bapsflib.utils.exceptions import HDFMappingError


class TestNIXZ(ControlTestCase):
    """Test class for HDFMapControlNIXZ"""

    # define setup variables
    DEVICE_NAME = "NI_XZ"
    DEVICE_PATH = "Raw data + config/NI_XZ"
    MAP_CLASS = HDFMapControlNIXZ

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test_contype(self):
        self.assertEqual(self.map.info["contype"], ConType.motion)

    def test_map_failures(self):
        """Test conditions that result in unsuccessful mappings."""
        # any failed build must throw a HDFMappingError
        #
        # 1. 'Run time list' is missing
        # 2. dataset is missing 'Shot number' field
        # 3. dataset is missing 'x' and 'z' fields
        #
        # make a default/clean 'NI_XZ' module
        self.mod.knobs.reset()

        # dataset 'Run time list' missing                            (1)
        # - rename 'Run time list' dataset
        self.mod.move("Run time list", "NIXZ data")
        with self.assertRaises(HDFMappingError):
            _map = self.map
        self.mod.move("NIXZ data", "Run time list")

        # dataset missing 'Shot number' field                        (2)
        self.mod.move("Run time list", "NIXZ data")
        odata = self.mod["NIXZ data"][...]
        fields = list(odata.dtype.names)
        fields.remove("Shot number")
        data = odata[fields]
        self.mod.create_dataset("Run time list", data=data)
        with self.assertRaises(HDFMappingError):
            _map = self.map
        del self.mod["Run time list"]
        self.mod.move("NIXZ data", "Run time list")

        # dataset missing 'x' and 'z' fields                         (3)
        self.mod.move("Run time list", "NIXZ data")
        odata = self.mod["NIXZ data"][...]
        fields = list(odata.dtype.names)
        fields.remove("x")
        fields.remove("z")
        data = odata[fields]
        self.mod.create_dataset("Run time list", data=data)
        with self.assertRaises(HDFMappingError):
            _map = self.map
        del self.mod["Run time list"]
        self.mod.move("NIXZ data", "Run time list")

    def test_map_warnings(self):
        """Test conditions that issue a UserWarning"""
        # Warnings relate to unexpected behavior that does not affect
        # reading of data from the HDF5 file
        #
        # 1. No motion list group is found
        # 2. motion list group is missing an attribute
        # 3. dataset 'Run time list' is missing one of 'x' or 'z' fields
        #
        # make a default/clean 'NI_XZ' module
        self.mod.knobs.reset()

        # no motion list group is found                              (1)
        del self.mod["ml-0001"]
        with self.assertWarns(UserWarning):
            _map = self.map
            self.assertNIXZDetails(_map, self.dgroup)
        self.mod.knobs.reset()

        # motion list group is missing an attribute                  (2)
        del self.mod["ml-0001"].attrs["Nx"]
        with self.assertWarns(UserWarning):
            _map = self.map
            self.assertNIXZDetails(_map, self.dgroup)
        self.mod.knobs.reset()

        # dataset 'Run time list' is missing one of 'x' or 'z'       (3)
        # fields
        self.mod.move("Run time list", "NIXZ data")
        odata = self.mod["NIXZ data"][...]
        fields = list(odata.dtype.names)
        fields.remove("x")
        data = odata[fields]
        self.mod.create_dataset("Run time list", data=data)
        del self.mod["NIXZ data"]
        with self.assertWarns(UserWarning):
            _map = self.map
            self.assertNIXZDetails(_map, self.dgroup)
        self.mod.knobs.reset()

    def test_misc(self):
        """Test miscellaneous behavior"""
        # 1. there are 2 motion list groups
        # 2. motion list group is missing all key attributes
        #
        # make a default/clean 'NI_XZ' module
        self.mod.knobs.reset()

        # there are 2 motion list groups                             (1)
        self.mod.knobs.n_motionlists = 2
        _map = self.map
        self.assertNIXZDetails(_map, self.dgroup)
        for name in self.mod.configs["config01"]["motion lists"]:
            self.assertIn(name, _map.configs["config01"]["motion lists"])
        self.mod.knobs.reset()

        # motion list group is missing all key attributes            (2)
        # key attributes: Nx, Nz, dx, dz, x0, z0
        self.mod.knobs.n_motionlists = 2
        for key in ("Nx", "Nz", "dx", "dz", "x0", "z0"):
            del self.mod["ml-0001"].attrs[key]
        _map = self.map
        self.assertNIXZDetails(_map, self.dgroup)
        self.assertNotIn("ml-0001", _map.configs["config01"]["motion lists"])
        self.assertIn("ml-0002", _map.configs["config01"]["motion lists"])

    def assertNIXZDetails(self, _map: HDFMapControlNIXZ, _group: h5py.Group):
        """Assert details of the 'NI_XZ' mapping."""
        # confirm basics
        self.assertControlMapBasics(_map, _group)

        # check dataset names
        self.assertEqual(_map.construct_dataset_name(), "Run time list")

        # no command list
        self.assertFalse(_map.has_command_list)

        # there only ever one configuration
        self.assertEqual(len(_map.configs), 1)
        self.assertEqual(list(_map.configs), ["config01"])
        self.assertTrue(_map.one_config_per_dset)

        # test general item sin configs
        self.assertNIXZConfigItems(_map)

    def assertNIXZConfigItems(self, _map):
        """
        Test structure of the general, polymorphic elements of the
        `configs` mapping dictionary
        """
        config = _map.configs["config01"]
        self.assertIn("motion lists", config)
        self.assertIsInstance(config["motion lists"], dict)


if __name__ == "__main__":
    ut.main()
