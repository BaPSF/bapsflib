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
import re
import unittest as ut

from bapsflib._hdf.maps import FauxHDFBuilder
from bapsflib._hdf.maps.controls import ConType
from bapsflib._hdf.maps.controls.templates import (
    HDFMapControlCLTemplate,
    HDFMapControlTemplate,
)


def method_overridden(cls, obj, method: str) -> bool:
    """check if obj's class over-road base class method"""
    obj_method = method in obj.__class__.__dict__.keys()
    base_method = method in cls.__dict__.keys()
    return obj_method and base_method


class ControlTestCase(ut.TestCase):
    """
    TestCase for control devices.
    """

    # TODO: DESIGN A FAILURES TEST 'test_map_failures'
    # - These are required scenarios where the mapping class should
    #   raise a HDFMappingError

    f = NotImplemented
    DEVICE_NAME = NotImplemented
    DEVICE_PATH = NotImplemented
    MAP_CLASS = NotImplemented

    @classmethod
    def setUpClass(cls):
        # skip tests if in ControlTestCase
        if cls is ControlTestCase:
            raise ut.SkipTest("In ControlTestCase, skipping base tests")
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
        self.assertControlMapBasics(self.map, self.dgroup)

    def test_not_h5py_group(self):
        """Test error if object to map is not h5py.Group"""
        with self.assertRaises(TypeError):
            self.map_device(None)

    def assertControlMapBasics(self, _map, _group):
        # check mapping instance
        self.assertIsInstance(_map, HDFMapControlTemplate)

        # assert attribute existence
        self.assertTrue(hasattr(_map, "info"))
        self.assertTrue(hasattr(_map, "configs"))
        self.assertTrue(hasattr(_map, "contype"))
        self.assertTrue(hasattr(_map, "device_name"))
        self.assertTrue(hasattr(_map, "group"))
        self.assertTrue(hasattr(_map, "subgroup_names"))
        self.assertTrue(hasattr(_map, "dataset_names"))
        self.assertTrue(hasattr(_map, "has_command_list"))
        self.assertTrue(hasattr(_map, "one_config_per_dset"))
        self.assertTrue(hasattr(_map, "construct_dataset_name"))

        # check 'has_command_list'
        # - `has_command_list` should only be true if the mapping class
        #   subclassed HDFMapControlCLTemplate
        #
        self.assertIsInstance(_map.has_command_list, bool)
        self.assertFalse(
            isinstance(_map, HDFMapControlCLTemplate) ^ _map.has_command_list
        )

        # ---- test map.info                                        ----
        # test 'info' type
        self.assertIsInstance(_map.info, dict)

        # check 'info' keys
        self.assertIn("group name", _map.info)
        self.assertIn("group path", _map.info)
        self.assertIn("contype", _map.info)

        # check 'info' values
        self.assertEqual(_map.info["group name"], os.path.basename(_group.name))
        self.assertEqual(_map.info["group path"], _group.name)
        self.assertIsInstance(_map.info["contype"], ConType)

        # ---- test general attributes                              ----
        # check 'contype'
        self.assertEqual(_map.info["contype"], _map.contype)

        # check 'device_name'
        self.assertEqual(_map.device_name, _map.info["group name"])

        # check 'group'
        self.assertIsInstance(_map.group, h5py.Group)
        self.assertEqual(_map.group, _group)

        # check 'subgroup_names' (sub-group names)
        self.assertSubgroupNames(_map, _group)

        # check 'dataset_names'
        self.assertDatasetNames(_map, _group)

        # check 'one_config_per_dset'
        self.assertIsInstance(_map.one_config_per_dset, bool)
        self.assertFalse(
            len(_map.dataset_names) == len(_map.configs) ^ _map.one_config_per_dset
        )

        # ---- test map.configs                                     ----
        #
        # - The `configs` dictionary contains the translation info
        #   in-order to translate the data stored in the HDF5 datasets
        #   to the structure numpy array constructed by HDFReadControls
        #
        # - Each item in `configs` must be structured as:
        #     Key == name of configuration
        #     Value == configuration dictionary (config_dict)
        #
        # - The keys in the config_dict breakdown into 3 categories
        #   1. translation keys
        #      ('shotnum' and 'state values')
        #
        #      ~ these keys are used by HDFReadControls and contain the
        #        the necessary info to translate the data from the HDF5
        #        datasets to the structured numpy array
        #
        #   2. translation support keys
        #      ('dset paths')
        #
        #      ~ these keys are used to support the data translation by
        #        HDFReadControls and are also considered meta-info for
        #        the Control Device
        #      ~ meta-info keys are added to the `info` dictionary
        #        attribute that is bound to the numpy array data object
        #        constructed by HDFReadControls
        #
        #   3. meta-info keys
        #
        #      ~ not used in the translation, are considered meta-info
        #        for the Control Device
        #      ~ meta-info keys are added to the `info` dictionary
        #        attribute that is bound to the numpy array data object
        #        constructed by HDFReadControls
        #
        self.assertIsInstance(_map.configs, dict)
        for config_name, config in _map.configs.items():
            # must be a dict
            self.assertIsInstance(config, dict)

            # look for required keys
            # - Note: 'command list' is only required for CL controls
            #         and is covered by assertAdditionalCLRequirements
            self.assertIn("dset paths", config)
            self.assertIn("shotnum", config)
            self.assertIn("state values", config)

            # -- examine 'dset paths' --
            self.assertIsInstance(config["dset paths"], tuple)
            self.assertTrue(len(config["dset paths"]), 1)
            self.assertIsInstance(config["dset paths"][0], str)

            # -- examine 'shotnum' key --
            # required keys
            self.assertIsInstance(config["shotnum"], dict)
            self.assertIn("dset paths", config["shotnum"])
            self.assertIn("dset field", config["shotnum"])
            self.assertIn("shape", config["shotnum"])
            self.assertIn("dtype", config["shotnum"])

            # ['shotnum']['dset paths']
            self.assertEqual(config["shotnum"]["dset paths"], config["dset paths"])

            # ['shotnum']['dset field']
            self.assertIsInstance(config["shotnum"]["dset field"], tuple)
            self.assertEqual(len(config["shotnum"]["dset field"]), 1)
            self.assertIsInstance(config["shotnum"]["dset field"][0], str)

            # ['shotnum']['shape']
            self.assertEqual(config["shotnum"]["shape"], ())

            # ['shotnum']['dtype']
            self.assertTrue(np.issubdtype(config["shotnum"]["dtype"], np.integer))

            # -- examine 'state values' key --
            self.assertIsInstance(config["state values"], dict)
            for sv_name, sv_config in config["state values"].items():
                self.assertSVConfig(sv_name, sv_config, config, what="default")

        # do additional checks for 'command list' (CL) focused devices
        if _map.has_command_list:
            # noinspection PyTypeChecker
            self.assertAdditionalCLRequirements(_map, _group)

    def assertAdditionalCLRequirements(self, _map, _group):
        # check subclassing from CL template
        self.assertIsInstance(_map, HDFMapControlCLTemplate)

        # assert CL attributes
        self.assertTrue(hasattr(_map, "_default_re_patterns"))
        self.assertTrue(hasattr(_map, "_default_state_values_dict"))
        self.assertTrue(hasattr(_map, "_construct_state_values_dict"))
        self.assertTrue(hasattr(_map, "clparse"))
        self.assertTrue(hasattr(_map, "reset_state_values_config"))
        self.assertTrue(hasattr(_map, "set_state_values_config"))

        # ---- test general attributes                              ----
        # examine '_default_re_patterns'
        self.assertIsInstance(_map._default_re_patterns, tuple)
        for pattern in _map._default_re_patterns:
            self.assertIsInstance(pattern, str)
            pat = re.compile(pattern)
            self.assertEqual(len(pat.groupindex), 2)
            self.assertIn("VAL", pat.groupindex.keys())

        # examine '_default_state_values_dict'
        for config_name in _map.configs:
            default_sv_dict = _map._default_state_values_dict(config_name)
            self.assertIsInstance(default_sv_dict, dict)
            for sv_name, sv_config in default_sv_dict.items():
                self.assertSVConfig(
                    sv_name, sv_config, _map.configs[config_name], what="cl"
                )

        # examine remaining attributes
        methods = (
            "_construct_state_values_dict",
            "clparse",
            "reset_state_values_config",
            "set_state_values_config",
        )
        for method in methods:
            self.assertFalse(
                method_overridden(HDFMapControlCLTemplate, _map, method),
                msg=f"Overriding HDFMapControlCLTemplate method '{method}' not allowed",
            )

        # ---- test map.configs                                     ----
        for config_name, config in _map.configs.items():
            # check for required keys
            self.assertIn("command list", config)

            # check 'command list'
            self.assertIsInstance(config["command list"], tuple)
            self.assertNotEqual(len(config["command list"]), 0)
            self.assertTrue(
                all(isinstance(command, str) for command in config["command list"])
            )

            # -- examine 'state values' key --
            for sv_name, sv_config in config["state values"].items():
                self.assertSVConfig(sv_name, sv_config, config, what="cl only")

    def assertSVConfig(self, sv_name, sv_config, config, what="default"):
        # 'default' = checks just required elements for a non command
        #             list control device
        # 'cl' =      check all required elements for a command list
        #             device
        # 'cl only' = check only required elements specific to a
        #             control device
        # is a dict
        self.assertIsInstance(sv_config, dict)

        if what not in ("default", "cl", "cl only"):
            raise ValueError(
                f"Keyword 'what' given as '{what}', but expected 'default', 'cl',"
                f" or 'cl only'."
            )

        # 'state value' can NOT be called 'signal'
        # - this is reserved for the signal field created by HDFReadData
        #
        self.assertNotEqual(sv_name, "signal")

        # -- check absolutely required elements                     ----
        if what in ("default", "cl"):
            # required keys
            # - Note: 'command list', 'cl str', and 're pattern'
            #         is only required for CL controls and is
            #         covered by assertAdditionalCLRequirements
            self.assertIn("dset paths", sv_config)
            self.assertIn("dset field", sv_config)
            self.assertIn("shape", sv_config)
            self.assertIn("dtype", sv_config)

            # ['state values']['']['dset paths']
            self.assertEqual(sv_config["dset paths"], config["dset paths"])

            # ['state values']['']['dset field']
            self.assertIsInstance(sv_config["dset field"], tuple)
            self.assertNotEqual(len(sv_config["dset field"]), 0)
            self.assertTrue(
                all(isinstance(field, str) for field in sv_config["dset field"])
            )

            # ['state values]['']['shape']
            self.assertIsInstance(sv_config["shape"], tuple)
            self.assertTrue(all(isinstance(val, int) for val in sv_config["shape"]))
            if len(sv_config["shape"]) == 0:
                self.assertEqual(len(sv_config["dset field"]), 1)
            else:
                self.assertIn(len(sv_config["dset field"]), (1, sv_config["shape"][0]))

            # ['state values]['']['dtype']
            # - 'dtype' must be convertible by np.dtype
            try:
                np.dtype(sv_config["dtype"])
            except TypeError as err:
                self.fail(
                    f"({err})\nconfigs['state values']['{sv_name}']['dtype']' needs "
                    f"to be convertible by numpy.dtype"
                )

        # -- check absolutely required elements                     ----
        if what in ("cl only", "cl"):
            # required keys
            self.assertIn("command list", sv_config)
            self.assertIn("cl str", sv_config)
            self.assertIn("re pattern", sv_config)

            # ['state values']['']['command list']
            # - the matched 'command list' value
            self.assertIsInstance(sv_config["command list"], tuple)
            self.assertEqual(len(sv_config["command list"]), len(config["command list"]))
            self.assertTrue(
                all(
                    isinstance(command, type(sv_config["command list"][0]))
                    for command in sv_config["command list"]
                )
            )
            self.assertIsInstance(sv_config["command list"][0], (str, float))

            # ['state values']['']['cl str']
            # - the resulting string from the RE
            self.assertIsInstance(sv_config["cl str"], tuple)
            self.assertEqual(len(sv_config["cl str"]), len(config["command list"]))
            self.assertTrue(all(isinstance(clstr, str) for clstr in sv_config["cl str"]))

            # ['state values']['']['re pattern']
            # - the RE pattern used for matching against the
            #   original command list
            self.assertIsInstance(
                sv_config["re pattern"], (type(None), type(re.compile(r"")))
            )

    def assertSubgroupNames(self, _map, _group):
        sgroup_names = [name for name in _group if isinstance(_group[name], h5py.Group)]
        self.assertEqual(_map.subgroup_names, sgroup_names)

    def assertDatasetNames(self, _map, _group):
        dset_names = [name for name in _group if isinstance(_group[name], h5py.Dataset)]
        self.assertEqual(_map.dataset_names, dset_names)
