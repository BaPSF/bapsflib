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
import astropy.units as u
import h5py
import unittest as ut

from bapsflib._hdf.maps.controls import ConType
from bapsflib._hdf.maps.controls.nixyz import HDFMapControlNIXYZ
from bapsflib._hdf.maps.controls.tests.common import ControlTestCase
from bapsflib.utils.exceptions import HDFMappingError


class TestNIXYZ(ControlTestCase):
    """Test class for HDFMapControlNIXYZ"""

    # define setup variables
    DEVICE_NAME = "NI_XYZ"
    DEVICE_PATH = "Raw data + config/NI_XYZ"
    MAP_CLASS = HDFMapControlNIXYZ

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
        # 3. dataset is missing 'x', 'y' and 'z' fields
        #
        # make a default/clean 'NI_XYZ' module
        self.mod.knobs.reset()

        # dataset 'Run time list' missing                            (1)
        # - rename 'Run time list' dataset
        self.mod.move("Run time list", "NIXYZ data")
        with self.assertRaises(HDFMappingError):
            _map = self.map
        self.mod.move("NIXYZ data", "Run time list")

        # dataset missing 'Shot number' field                        (2)
        self.mod.move("Run time list", "NIXYZ data")
        odata = self.mod["NIXYZ data"][...]
        fields = list(odata.dtype.names)
        fields.remove("Shot number")
        data = odata[fields]
        self.mod.create_dataset("Run time list", data=data)
        with self.assertRaises(HDFMappingError):
            _map = self.map
        del self.mod["Run time list"]
        self.mod.move("NIXYZ data", "Run time list")

        # dataset missing 'x', 'y' and 'z' fields                    (3)
        self.mod.move("Run time list", "NIXYZ data")
        odata = self.mod["NIXYZ data"][...]
        fields = list(odata.dtype.names)
        fields.remove("x")
        fields.remove("y")
        fields.remove("z")
        data = odata[fields]
        self.mod.create_dataset("Run time list", data=data)
        with self.assertRaises(HDFMappingError):
            _map = self.map
        del self.mod["Run time list"]
        self.mod.move("NIXYZ data", "Run time list")

    def test_map_warnings(self):
        """Test conditions that issue a UserWarning"""
        # Warnings relate to unexpected behavior that does not affect
        # reading of data from the HDF5 file
        #
        # 1. No motion list group is found
        # 2. motion list group is missing an attribute
        # 3. dataset 'Run time list' is missing one of 'x', 'y' or
        #    'z' fields
        #
        # make a default/clean 'NI_XYZ' module
        self.mod.knobs.reset()

        # no motion list group is found                              (1)
        del self.mod["ml-0001"]
        with self.assertWarns(UserWarning):
            _map = self.map
            self.assertNIXYZDetails(_map, self.dgroup)
        self.mod.knobs.reset()

        # motion list group is missing an attribute                  (2)
        del self.mod["ml-0001"].attrs["Nx"]
        with self.assertWarns(UserWarning):
            _map = self.map
            self.assertNIXYZDetails(_map, self.dgroup)
        self.mod.knobs.reset()

        # dataset 'Run time list' is missing one of 'x', 'y'         (3)
        # or 'z' fields
        self.mod.move("Run time list", "NIXYZ data")
        odata = self.mod["NIXYZ data"][...]
        fields = list(odata.dtype.names)
        fields.remove("x")
        fields.remove("y")
        data = odata[fields]
        self.mod.create_dataset("Run time list", data=data)
        del self.mod["NIXYZ data"]
        with self.assertWarns(UserWarning):
            _map = self.map
            self.assertNIXYZDetails(_map, self.dgroup)
        self.mod.knobs.reset()

    def test_misc(self):
        """Test miscellaneous behavior"""
        # 1. there are 2 motion list groups
        # 2. motion list group is missing all key attributes
        #
        # make a default/clean 'NI_XYZ' module
        self.mod.knobs.reset()

        # there are 2 motion list groups                             (1)
        self.mod.knobs.n_motionlists = 2
        _map = self.map
        self.assertNIXYZDetails(_map, self.dgroup)
        for name in self.mod.configs["config01"]["motion lists"]:
            self.assertIn(name, _map.configs["config01"]["motion lists"])
        self.mod.knobs.reset()

        # motion list group is missing all key attributes            (2)
        # key attributes: Nx, Ny, Nz, dx, dy, dz, x0, y0, z0
        self.mod.knobs.n_motionlists = 2
        for key in ("Nx", "Ny", "Nz", "dx", "dy", "dz", "x0", "y0", "z0"):
            del self.mod["ml-0001"].attrs[key]
        _map = self.map
        self.assertNIXYZDetails(_map, self.dgroup)
        self.assertNotIn("ml-0001", _map.configs["config01"]["motion lists"])
        self.assertIn("ml-0002", _map.configs["config01"]["motion lists"])

    def assertNIXYZDetails(self, _map: HDFMapControlNIXYZ, _group: h5py.Group):
        """Assert details of the 'NI_XYZ' mapping."""
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
        self.assertNIXYZConfigItems(_map)

    def assertNIXYZConfigItems(self, _map):
        """
        Test structure of the general, polymorphic elements of the
        `configs` mapping dictionary
        """
        config = _map.configs["config01"]
        self.assertIn("motion lists", config)
        self.assertIsInstance(config["motion lists"], dict)
        self.assertIn("Note", config)
        self.assertIsInstance(config["Note"], str)
        self.assertIn("Lpp", config)
        self.assertEqual(config["Lpp"], 58.771 * u.cm)


if __name__ == "__main__":
    ut.main()
