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
import astropy.units as u
import h5py
import numpy as np
import os
import unittest as ut

from typing import Tuple

from bapsflib._hdf.maps import FauxHDFBuilder
from bapsflib._hdf.maps.digitizers.templates import HDFMapDigiTemplate


def method_overridden(cls, obj, method: str) -> bool:
    """check if obj's class over-road base class method"""
    obj_method = method in obj.__class__.__dict__.keys()
    base_method = method in cls.__dict__.keys()
    return obj_method and base_method


class DigitizerTestCase(ut.TestCase):
    """Base TestCase for testing digitizer mapping classes."""

    # TODO: DESIGN A FAILURES TEST 'test_map_failures'
    # - These are required scenarios where the mapping class should
    #   raise a HDFMappingError

    f = NotImplemented  # type: FauxHDFBuilder
    DEVICE_NAME = NotImplemented  # type: str
    DEVICE_PATH = NotImplemented  # type: str
    MAP_CLASS = NotImplemented

    @classmethod
    def setUpClass(cls):
        # skip tests if in MSIDiagnosticTestCase
        if cls is DigitizerTestCase:
            raise ut.SkipTest("In DigitizerTestCase, skipping base tests")
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
    def map(self) -> HDFMapDigiTemplate:
        """Map object of device"""
        return self.map_device(self.dgroup)

    @property
    def dgroup(self) -> h5py.Group:
        """Device HDF5 group"""
        return self.f[self.DEVICE_PATH]

    def map_device(self, group: h5py.Group) -> HDFMapDigiTemplate:
        """Mapping function"""
        return self.MAP_CLASS(group)

    def test_map_basics(self):
        """Test all required basic map features."""
        self.assertDigitizerMapBasics(self.map, self.dgroup)

    def test_not_h5py_group(self):
        """Test error if object to map is not h5py.Group"""
        with self.assertRaises(TypeError):
            self.map_device(None)

    def assertDigitizerMapBasics(self, _map: HDFMapDigiTemplate, _group: h5py.Group):
        # check instance
        self.assertIsInstance(_map, HDFMapDigiTemplate)

        # assert attribute existence
        self.assertTrue(hasattr(_map, "_build_configs"))
        self.assertTrue(hasattr(_map, "active_configs"))
        self.assertTrue(hasattr(_map, "configs"))
        self.assertTrue(hasattr(_map, "construct_dataset_name"))
        self.assertTrue(hasattr(_map, "construct_header_dataset_name"))
        self.assertTrue(hasattr(_map, "deduce_config_active_status"))
        self.assertTrue(hasattr(_map, "device_adcs"))
        self.assertTrue(hasattr(_map, "device_name"))
        self.assertTrue(hasattr(_map, "get_adc_info"))
        self.assertTrue(hasattr(_map, "group"))
        self.assertTrue(hasattr(_map, "info"))

        # ---- test general attributes (part 1 of 2)                ----
        # 'device_adcs'
        # 'device_name'
        # 'group'
        #
        # check `device_adcs`
        self.assertIsInstance(_map.device_adcs, tuple)
        self.assertTrue(bool(_map.device_adcs))
        self.assertTrue(all(isinstance(adc, str) for adc in _map.device_adcs))

        # check `device_name`
        self.assertEqual(_map.device_name, _map.info["group name"])

        # check `group`
        self.assertIsInstance(_map.group, h5py.Group)
        self.assertEqual(_map.group, _group)

        # ---- test map.info                                        ----
        # type
        self.assertIsInstance(_map.info, dict)

        # key existence
        self.assertIn("group name", _map.info)
        self.assertIn("group path", _map.info)

        # values
        self.assertEqual(_map.info["group name"], os.path.basename(_group.name))
        self.assertEqual(_map.info["group path"], _group.name)

        # ---- test map.configs                                     ----
        #
        # - The `configs` dictionary contains the translation info
        #   in-order to translate the data stored in the HDF5 datasets
        #   to the structure numpy array constructed by HDFReadData
        #
        # - Each item in `configs` must be structured as:
        #     Key == name of configuration
        #     Value == configuration dictionary (config_dict)
        #
        # - The keys in the config_dict breakdown into 2 categories:
        #   1. Required, which breakdown into 2 sub-categories
        #
        #      A. non-polymorphic keys
        #         ('active', 'adc', 'config group path', and 'shotnum')
        #      B. polymorphic keys
        #         ~ these keys are the adc names listed in the 'adc' key
        #
        #      ~ these keys are used by HDFReadData to translate data
        #        from the HDF5 file into a structured numpy array
        #
        #   2. Optional meta-info keys
        #
        #      ~ not used in the translation, are considered meta-info
        #        for the Digitizer
        #      ~ meta-info keys are added to the `info` dictionary
        #        attribute that is bound to the numpy array data object
        #        constructed by HDFReadControls
        #
        self.assertIsInstance(_map.configs, dict)
        for cname, config in _map.configs.items():
            # must be a dict
            self.assertIsInstance(config, dict)

            # look for required keys
            # - polymorphic keys are examined below in the section
            #   "examine polymorphic "adc" keys"
            #
            self.assertIn("active", config)
            self.assertIn("adc", config)
            self.assertIn("config group path", config)
            self.assertIn("shotnum", config)

            # examine 'active' key
            self.assertIsInstance(config["active"], bool)

            # examine 'adc' key
            self.assertIsInstance(config["adc"], tuple)
            for adc in config["adc"]:
                self.assertIsInstance(adc, str)
                self.assertIn(adc, _map.device_adcs)

            # examine 'config group path' key
            self.assertIsInstance(config["config group path"], str)
            self.assertIsNotNone(_group.get(config["config group path"]))

            # -- examine 'shotnum' key --
            # required keys
            self.assertIsInstance(config["shotnum"], dict)
            self.assertIn("dset field", config["shotnum"])
            self.assertIn("shape", config["shotnum"])
            self.assertIn("dtype", config["shotnum"])

            # ['shotnum']['dset field']
            self.assertIsInstance(config["shotnum"]["dset field"], tuple)
            self.assertEqual(len(config["shotnum"]["dset field"]), 1)
            self.assertIsInstance(config["shotnum"]["dset field"][0], str)

            # ['shotnum']['shape']
            self.assertEqual(config["shotnum"]["shape"], ())

            # ['shotnum']['dtype']
            self.assertTrue(np.issubdtype(config["shotnum"]["dtype"], np.integer))

            # -- examine polymorphic "adc" keys --
            for adc in config["adc"]:
                # is a tuple of 3-element tuples
                self.assertIsInstance(config[adc], tuple)
                self.assertTrue(bool(config[adc]))
                for conn in config[adc]:
                    self.assertIsInstance(conn, tuple)
                    self.assertEqual(len(conn), 3)

                    # 1st element is board number
                    self.assertIsInstance(conn[0], (int, np.integer))

                    # 2nd element is tuple of active channels on board
                    self.assertIsInstance(conn[1], tuple)
                    self.assertTrue(bool(conn[1]))
                    self.assertTrue(
                        all(isinstance(ch, (int, np.integer)) for ch in conn[1])
                    )

                    # 3rd element is dict of setup parameters
                    self.assertIsInstance(conn[2], dict)
                    self.assertIn("bit", conn[2])
                    self.assertIn("clock rate", conn[2])
                    self.assertIn("nshotnum", conn[2])
                    self.assertIn("nt", conn[2])
                    self.assertIn("shot average (software)", conn[2])
                    self.assertIn("sample average (hardware)", conn[2])

                    # check 'bit'
                    self.assertIsInstance(conn[2]["bit"], (int, np.integer))
                    self.assertTrue(conn[2]["bit"] > 0)

                    # check 'clock rate'
                    self.assertIsInstance(conn[2]["clock rate"], u.Quantity)
                    # noinspection PyUnresolvedReferences
                    self.assertTrue(conn[2]["clock rate"].unit.is_equivalent(u.Hertz))

                    # check 'nshotnum' and 'nt'
                    for key in ("nshotnum", "nt"):
                        self.assertIsInstance(conn[2][key], (int, np.integer))
                        self.assertTrue(conn[2][key] > 0 or conn[2][key] == -1)

                    # check 'shot average' and 'sample average'
                    for key in ("shot average (software)", "sample average (hardware)"):
                        self.assertIsInstance(conn[2][key], (type(None), int, np.integer))
                        if conn[2][key] is not None:
                            self.assertFalse(conn[2][key] <= 1)

        """
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
        """

        # ---- test general attributes (part 2 of 2)                ----
        # 'active_configs'
        # 'construct_dataset_name'
        # 'construct_header_dataset_name'
        # 'deduce_config_active_status'
        # 'get_adc_info'
        #
        # check `active_configs`
        self.assertIsInstance(_map.active_configs, list)
        self.assertTrue(bool(_map.active_configs))
        for active in _map.active_configs:
            self.assertIsInstance(active, str)
            self.assertTrue(_map.configs[active]["active"])

        # check `construct_dataset_name`
        self.assertConstructDatasetName(_map, _group)

        # check `construct_header_dataset_name`
        self.assertConstructHeaderDatasetName(_map, _group)

        # check `deduce_config_active_status`
        for cname in _map.configs:
            active_status = _map.deduce_config_active_status(cname)
            self.assertIsInstance(active_status, bool)
            self.assertEqual(active_status, _map.configs[cname]["active"])

        # check `get_adc_info`
        self.assertFalse(
            method_overridden(HDFMapDigiTemplate, _map, "get_adc_info"),
            msg="Overriding HDFMapDigiTemplate method 'get_adc_info' is NOT allowed",
        )

    def assertConstructDatasetName(self, _map: HDFMapDigiTemplate, _group: h5py.Group):
        """Assert all expected datasets exist"""
        # build kwargs groupings
        kwargs_list = []
        for cname, config in _map.configs.items():
            for adc in config["adc"]:
                for conn in config[adc]:
                    brd = conn[0]
                    chs = conn[1]

                    for ch in chs:
                        kwargs_list.append(
                            {
                                "board": brd,
                                "channel": ch,
                                "config_name": cname,
                                "adc": adc,
                                "return_info": False,
                            }
                        )

        for kwargs in kwargs_list:
            if kwargs["config_name"] not in _map.active_configs:
                with self.assertRaises(ValueError):
                    _map.construct_dataset_name(**kwargs)
            else:
                # -- usage without setup info dict --
                dset_name = _map.construct_dataset_name(**kwargs)
                self.assertIsInstance(dset_name, str)
                self.assertIsNotNone(_group.get(dset_name))

                # -- usage with setup info dict --
                kwargs["return_info"] = True
                stuff = _map.construct_dataset_name(**kwargs)
                self.assertIsInstance(stuff, tuple)
                self.assertEqual(len(stuff), 2)
                self.assertEqual(stuff[0], dset_name)
                self.assertIsInstance(stuff[1], dict)

    def assertConstructHeaderDatasetName(
        self, _map: HDFMapDigiTemplate, _group: h5py.Group
    ):
        """Assert all expected header datasets exist"""
        # build kwargs groupings
        kwargs_list = []
        for cname, config in _map.configs.items():
            for adc in config["adc"]:
                for conn in config[adc]:
                    brd = conn[0]
                    chs = conn[1]

                    for ch in chs:
                        kwargs_list.append(
                            {
                                "board": brd,
                                "channel": ch,
                                "config_name": cname,
                                "adc": adc,
                            }
                        )

        for kwargs in kwargs_list:
            if kwargs["config_name"] not in _map.active_configs:
                with self.assertRaises(ValueError):
                    _map.construct_dataset_name(**kwargs)
            else:
                # -- usage without setup info dict --
                dset_name = _map.construct_dataset_name(**kwargs)
                self.assertIsInstance(dset_name, str)
                self.assertIsNotNone(_group.get(dset_name))

    def assertConnectionsEqual(
        self,
        _map: HDFMapDigiTemplate,
        connections: Tuple[Tuple[int, Tuple[int, ...]], ...],
        adc: str,
        config_name: str,
    ):
        """
        Test equality of mapped adc connections and expected
        adc connections.
        """
        map_conns = _map.configs[config_name][adc]
        filter_conns = []
        for conn in map_conns:
            filter_conns.append((conn[0], conn[1]))
        map_conns = tuple(filter_conns)
        self.assertEqual(map_conns, connections)
