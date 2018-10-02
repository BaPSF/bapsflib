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

from bapsflib.lapd._hdf.tests import FauxHDFBuilder


class DigitizerTestCase(ut.TestCase):
    """Base TestCase for testing digitizer mapping classes."""
    # TODO: DESIGN A FAILURES TEST 'test_map_failures'
    # - These are required scenarios where the mapping class should
    #   raise a HDFMappingError

    f = NotImplemented    # type: FauxHDFBuilder
    DEVICE_NAME = NotImplemented  # type: str
    DEVICE_PATH = NotImplemented  # type: str
    MAP_CLASS = NotImplemented

    @classmethod
    def setUpClass(cls):
        # skip tests if in MSIDiagnosticTestCase
        if cls is DigitizerTestCase:
            raise ut.SkipTest("In DigitizerTestCase, "
                              "skipping base tests")
        super().setUpClass()

        # create HDF5 file
        cls.f = FauxHDFBuilder()

    def setUp(self):
        # setup HDF5 file
        if not (self.DEVICE_NAME in self.f.modules
                and len(self.f.modules) == 1):
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
        self.assertDigitizerMapBasics(self.map, self.dgroup)

    def test_not_h5py_group(self):
        """Test error if object to map is not h5py.Group"""
        with self.assertRaises(TypeError):
            self.map_device(None)

    def assertDigitizerMapBasics(self, _map, _group):
        # assert attribute existence
        self.assertTrue(hasattr(_map, 'info'))
        self.assertTrue(hasattr(_map, 'configs'))
        self.assertTrue(hasattr(_map, 'active_configs'))
        self.assertTrue(hasattr(_map, 'group'))
        self.assertTrue(hasattr(_map, 'shotnum_field'))
        self.assertTrue(hasattr(_map, 'construct_dataset_name'))
        self.assertTrue(hasattr(_map, 'construct_header_dataset_name'))

        # test type and keys for map.info
        self.assertIsInstance(_map.info, dict)
        self.assertIn('group name', _map.info)
        self.assertIn('group path', _map.info)

        # test map.configs
        # - must be a dict
        # - each key must have a dict value
        # - each sub-dict must have certain keys
        self.assertIsInstance(_map.configs, dict)
        for config in _map.configs:
            self.assertIsInstance(_map.configs[config], dict)
            self.assertIn('active', _map.configs[config])
            self.assertIn('adc', _map.configs[config])
            self.assertIn('group name', _map.configs[config])
            self.assertIn('group path', _map.configs[config])

            # check types
            self.assertIsInstance(_map.configs[config]['active'], bool)
            self.assertIsInstance(_map.configs[config]['adc'], list)
            self.assertIsInstance(
                _map.configs[config]['group name'], str)
            self.assertIsInstance(
                _map.configs[config]['group path'], str)

            # test adc details
            for adc in _map.configs[config]['adc']:
                self.assertIn(adc, _map.configs[config])
                self.assertIsInstance(_map.configs[config][adc], list)

                for item in _map.configs[config][adc]:
                    self.assertIsInstance(item, tuple)
                    self.assertTrue(len(item) == 3)
                    self.assertIsInstance(item[0], np.int_)
                    self.assertIsInstance(item[1], list)
                    self.assertIsInstance(item[2], dict)

                    # all channel values must be integers
                    self.assertTrue(
                        all(isinstance(ch, np.int_) for ch in item[1]))

                    # item extras
                    # TODO: detail test on each key
                    self.assertIn('bit', item[2])
                    self.assertIn('clock rate', item[2])
                    self.assertIn('nshotnum', item[2])
                    self.assertIn('nt', item[2])
                    self.assertIn('shot average (software)', item[2])
                    self.assertIn('sample average (hardware)', item[2])

        # assert attribute 'group' type
        self.assertIsInstance(_map.group, h5py.Group)

        # ------ Basic construct_dataset_name() Behavior ------
        #
        # 1. board is invalid (board = -1)
        # 2. channel is invalid (channel = -1)
        # 3. config_name is invalid (config_name='')
        # 4. adc is invalid (adc='')
        # 5. return_into=False returns string
        # 6. return_info=True returns 2-element tuple
        #
        # gather active map info
        config = _map.active_configs[0]
        adc = _map.configs[config]['adc'][0]
        brd = _map.configs[config][adc][0][0]
        ch = _map.configs[config][adc][0][1][0]

        # (1) invalid board number
        self.assertRaises(ValueError,
                          _map.construct_dataset_name, -1, 1)

        # (2) invalid channel number
        self.assertRaises(ValueError,
                          _map.construct_dataset_name, brd, -1)

        # (3) invalid config_name
        self.assertRaises(ValueError,
                          _map.construct_dataset_name,
                          brd, ch, config_name='')

        # (4) invalid adc
        self.assertRaises(ValueError,
                          _map.construct_dataset_name,
                          brd, ch, adc='')
        # (5) returned object must be string
        dname = _map.construct_dataset_name(brd, ch)
        self.assertIsInstance(dname, str)

        # (6) returned object must be 2-element tuple
        # 0 = is a string
        # 1 = is a dict
        #
        dname = _map.construct_dataset_name(brd, ch, return_info=True)
        self.assertIsInstance(dname, tuple)
        self.assertEqual(len(dname), 2)
        self.assertIsInstance(dname[0], str)
        self.assertIsInstance(dname[1], dict)
        self.assertIn('bit', dname[1])
        self.assertIn('clock rate', dname[1])
        self.assertIn('shot average (software)', dname[1])
        self.assertIn('sample average (hardware)', dname[1])
        self.assertIn('adc', dname[1])
        self.assertIn('configuration name', dname[1])
        self.assertIn('digitizer', dname[1])
