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
import os
import unittest as ut

from bapsflib._hdf.maps import FauxHDFBuilder
from bapsflib._hdf.maps.msi.templates import HDFMapMSITemplate


class MSIDiagnosticTestCase(ut.TestCase):
    # TODO: test all datasets define in a 'signals' item have the same shape
    # TODO: test all datasets define in a 'meta' item have the same shape
    # TODO: every 'dset path' of 'signals' and 'meta' should have the same length
    # TODO: add a 'test_map_failures' method
    # - this method is intended to be overwritten by inheriting test
    #   case
    # - by default, it will set self.fail() but print instruction on
    #   what mapping failures should be written into the mapping class
    #

    f = NotImplemented
    DEVICE_NAME = NotImplemented
    DEVICE_PATH = NotImplemented
    MAP_CLASS = NotImplemented

    @classmethod
    def setUpClass(cls):
        # skip tests if in MSIDiagnosticTestCase
        if cls is MSIDiagnosticTestCase:
            raise ut.SkipTest("In MSIDiagnosticTestCase, skipping base tests")
        super().setUpClass()

        # create HDF5 file
        cls.f = FauxHDFBuilder()

    def setUp(self):
        # setup HDF5 file
        if not (self.DEVICE_NAME in self.f.modules and len(self.f.modules) == 1):
            # clear HDF5 file and add module
            self.f.remove_all_modules()
            self.f.add_module(self.DEVICE_NAME)

        # define `mod` attribute
        self.mod = self.f.modules[self.DEVICE_NAME]

    def tearDown(self):
        # reset module
        self.mod.knobs.reset()

    @classmethod
    def tearDownClass(cls):
        # cleanup and close HDF5 file
        super().tearDownClass()
        cls.f.cleanup()

    @property
    def map(self):
        """Map object of device"""
        return self.map_device(self.dgroup)

    @property
    def dgroup(self):
        """Device HDF5 group"""
        return self.f[self.DEVICE_PATH]

    def map_device(self, group):
        """Mapping function"""
        return self.MAP_CLASS(group)

    def test_map_basics(self):
        """Test all required basic map features."""
        self.assertMSIDiagMapBasics(self.map, self.dgroup)

    def test_not_h5py_group(self):
        """Test error if object to map is not h5py.Group"""
        with self.assertRaises(TypeError):
            self.map_device(None)

    def assertMSIDiagMapBasics(self, _map, _group):
        # This assertion checks that the constructed mapping object
        # meets the expected format such that bapsflib's high-level
        # interface objects can utilized the mapping.
        #
        # check mapping instance
        self.assertIsInstance(_map, HDFMapMSITemplate)

        # assert attribute existence
        self.assertTrue(hasattr(_map, "info"))
        self.assertTrue(hasattr(_map, "device_name"))
        self.assertTrue(hasattr(_map, "group"))
        self.assertTrue(hasattr(_map, "configs"))

        # ---- test map.info                                        ----
        # test 'info' type
        self.assertIsInstance(_map.info, dict)

        # check 'info' keys
        self.assertIn("group name", _map.info)
        self.assertIn("group path", _map.info)

        # check 'info' values
        self.assertEqual(_map.info["group name"], os.path.basename(_group.name))
        self.assertEqual(_map.info["group path"], _group.name)

        # ---- test map.device_name                                 ----
        self.assertEqual(_map.device_name, _map.info["group name"])

        # ---- test map.group                                       ----
        # check 'group' type
        self.assertIsInstance(_map.group, h5py.Group)

        # ---- test map.configs                                     ----
        # - will not examine non-required keys since the the bapsflib=
        #   HDF5 interface does NOT depend on them
        #
        # - must be a dict
        self.assertIsInstance(_map.configs, dict)

        # look for required keys
        self.assertIn("shape", _map.configs)
        self.assertIn("shotnum", _map.configs)
        self.assertIn("signals", _map.configs)
        self.assertIn("meta", _map.configs)

        # -- examine 'shape' key --
        self.assertIsInstance(_map.configs["shape"], tuple)
        self.assertEqual(len(_map.configs["shape"]), 1)
        self.assertIsInstance(_map.configs["shape"][0], int)

        # -- examine 'shotnum' key --
        self.assertIsInstance(_map.configs["shotnum"], dict)
        self.assertIn("dset paths", _map.configs["shotnum"])
        self.assertIn("dset field", _map.configs["shotnum"])
        self.assertIn("shape", _map.configs["shotnum"])
        self.assertIn("dtype", _map.configs["shotnum"])

        # ['shotnum']['dset path']
        # - is a tuple of strings
        # - each dataset must have the same number of rows defined
        #   by configs['shape']
        self.assertIsInstance(_map.configs["shotnum"]["dset paths"], tuple)
        self.assertTrue(
            all([isinstance(path, str) for path in _map.configs["shotnum"]["dset paths"]])
        )

        # ['shotnum']['dset field']
        # - is a tuple of strings
        # - length 1 or length of 'dset paths'
        self.assertIsInstance(_map.configs["shotnum"]["dset field"], tuple)
        self.assertTrue(
            all(
                [
                    isinstance(field, str)
                    for field in _map.configs["shotnum"]["dset field"]
                ]
            )
        )
        self.assertTrue(
            len(_map.configs["shotnum"]["dset field"])
            in (1, len(_map.configs["shotnum"]["dset paths"]))
        )

        # ['shotnum']['shape']
        # - must be empty tuple
        self.assertEqual(_map.configs["shotnum"]["shape"], ())

        # ['shotnum']['dtype']
        self.assertTrue(np.issubdtype(_map.configs["shotnum"]["dtype"], np.integer))

        # -- examine 'signals' key --
        self.assertIsInstance(_map.configs["signals"], dict)
        for field, config in _map.configs["signals"].items():
            # must be a dict
            self.assertIsInstance(config, dict)

            # look for required keys
            self.assertIn("dset paths", config)
            self.assertIn("dset field", config)
            self.assertIn("shape", config)
            self.assertIn("dtype", config)

            # ['dset paths']
            self.assertIsInstance(config["dset paths"], tuple)
            self.assertTrue(all([isinstance(path, str) for path in config["dset paths"]]))

            # ['dset field']
            # - 'signals' do not correlate to datasets with fields
            self.assertFalse(bool(config["dset field"]))

            # ['shape']
            self.assertIsInstance(config["shape"], tuple)
            self.assertTrue(all(isinstance(val, int) for val in config["shape"]))

            # ['dtype']
            self.assertTrue(
                np.issubdtype(config["dtype"], np.integer)
                or np.issubdtype(config["dtype"], np.floating)
            )

        # -- examine 'meta' key --
        # TODO: remove 'shape' key
        self.assertIsInstance(_map.configs["meta"], dict)
        self.assertIn("shape", _map.configs["meta"])
        for field, config in _map.configs["meta"].items():
            if field == "shape":
                # key 'shape' will not be a numpy field, skip below
                # assertions
                continue

            # must be a dict
            self.assertIsInstance(config, dict)

            # look for required keys
            self.assertIn("dset paths", _map.configs["meta"][field])
            self.assertIn("dset field", _map.configs["meta"][field])
            self.assertIn("shape", _map.configs["meta"][field])
            self.assertIn("dtype", _map.configs["meta"][field])

            # ['dset paths']
            self.assertIsInstance(config["dset paths"], tuple)
            self.assertTrue(all([isinstance(path, str) for path in config["dset paths"]]))

            # ['dset field']
            # - 'meta' fields do correlate to datasets with fields
            self.assertIsInstance(config["dset field"], tuple)
            self.assertTrue(all([isinstance(path, str) for path in config["dset paths"]]))

            # ['shape']
            self.assertIsInstance(_map.configs["meta"][field]["shape"], tuple)
            self.assertTrue(all(isinstance(val, int) for val in config["shape"]))

            # ['dtype']
            self.assertTrue(
                np.issubdtype(config["dtype"], np.integer)
                or np.issubdtype(config["dtype"], np.floating)
            )

        # --- All datasets must have the same number of rows        ----
        # - rows corresponds the the number of shot number recordings
        #
        # collect data set paths
        dset_paths = list(_map.configs["shotnum"]["dset paths"])
        for subfield in ("signals", "meta"):
            for field, config in _map.configs[subfield].items():
                # TODO: delete this when shape is removed
                if field == "shape":
                    continue
                val = list(config["dset paths"])
                dset_paths.extend(val)
        dset_paths = list(set(dset_paths))

        # check all has same num. of rows
        for path in dset_paths:
            dset = _group.get(path)
            if dset.shape[0] != _map.configs["shape"][0]:
                self.fail(
                    "Not all all datasets have the same number "
                    "of rows, this should have raised a "
                    "`HDFMappingError`"
                )

        # ---         ----
