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

from bapsflib.lapd._hdf.tests import FauxHDFBuilder

from ..templates import (HDFMapControlTemplate,
                         HDFMapControlCLTemplate)


class ControlTestCase(ut.TestCase):
    """
    TestCase for control devices.
    """

    f = NotImplemented
    DEVICE_NAME = NotImplemented
    DEVICE_PATH = NotImplemented
    MAP_CLASS = NotImplemented

    @classmethod
    def setUpClass(cls):
        # skip tests if in MSIDiagnosticTestCase
        if cls is ControlTestCase:
            raise ut.SkipTest("In MSIDiagnosticTestCase, "
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
        self.assertControlMapBasics(self.map, self.dgroup)

    def test_not_h5py_group(self):
        """Test error if object to map is not h5py.Group"""
        with self.assertRaises(TypeError):
            self.map_device(None)

    def assertControlMapBasics(self, _map, _group):
        # check mapping instance
        self.assertIsInstance(_map, HDFMapControlTemplate)

        # assert attribute existence
        self.assertTrue(hasattr(_map, 'info'))
        self.assertTrue(hasattr(_map, 'configs'))
        self.assertTrue(hasattr(_map, 'contype'))
        self.assertTrue(hasattr(_map, 'device_name'))
        self.assertTrue(hasattr(_map, 'group'))
        self.assertTrue(hasattr(_map, 'subgroup_names'))
        self.assertTrue(hasattr(_map, 'dataset_names'))
        self.assertTrue(hasattr(_map, 'has_command_list'))
        self.assertTrue(hasattr(_map, 'one_config_per_dset'))
        self.assertTrue(hasattr(_map, 'construct_dataset_name'))

        # extra attributes for a command list (CL) focused device
        self.assertIsInstance(_map.has_command_list, bool)
        if _map.has_command_list:
            # check inherited form proper template
            self.assertIsInstance(_map, HDFMapControlCLTemplate)

            # assert CL attributes
            self.assertTrue(hasattr(_map, '_cl_re_patterns'))
            self.assertTrue(hasattr(_map,
                                    '_default_state_values_dict'))
            self.assertTrue(hasattr(_map,
                                    '_construct_state_values_dict'))
            self.assertTrue(hasattr(_map, 'clparse'))
            self.assertTrue(hasattr(_map, 'reset_state_values_config'))
            self.assertTrue(hasattr(_map, 'set_state_values_config'))

        # ---- test map.info                                        ----
        # test 'info' type
        self.assertIsInstance(_map.info, dict)

        # check 'info' keys
        self.assertIn('group name', _map.info)
        self.assertIn('group path', _map.info)
        self.assertIn('contype', _map.info)

        # check 'info' values
        self.assertEqual(_map.info['group name'],
                         os.path.basename(_group.name))
        self.assertEqual(_map.info['group path'], _group.name)
        self.assertIn(_map.info['contype'],
                      ['motion', 'waveform', 'power', 'timing',
                       'generic'])

        # ---- test general attributes                              ----
        # check 'contype'
        self.assertEqual(_map.info['contype'], _map.contype)

        # check 'device_name'
        self.assertEqual(_map.device_name, _map.info['group name'])

        # check 'group'
        self.assertIsInstance(_map.group, h5py.Group)
        self.assertEqual(_map.group, _group)

        # check 'subgroup_names' (sub-group names)
        self.assertSubgroupNames(_map, _group)

        # check 'dataset_names'
        self.assertDatasetNames(_map, _group)

        # check 'one_config_per_dset'
        self.assertIsInstance(_map.one_config_per_dset, bool)

        # ---- test map.configs                                     ----
        #
        # - The `configs` dictionary contains the translation info
        #   in-order to translate the data stored in the HDF5 datasets
        #   to the structure numpy array constructed by hdfReadControl
        #
        # - Each item in `configs` must be structured as:
        #     Key == name of configuration
        #     Value == configuration dictionary (config_dict)
        #
        # - The keys in the config_dict breakdown into 3 categories
        #   1. translation keys
        #      ('shotnum' and 'state values')
        #
        #      ~ these keys are used by hdfReadControl and contain the
        #        the necessary info to translate the data from the HDF5
        #        datasets to the structured numpy array
        #
        #   2. translation support keys
        #      ('dset paths')
        #
        #      ~ these keys are used to support the data translation by
        #        hdfReadControl and are also considered meta-info for
        #        the Control Device
        #      ~ meta-info keys are added to the `info` dictionary
        #        attribute that is bound to the numpy array data object
        #        constructed by hdfReadControl
        #
        #   3. meta-info keys
        #
        #      ~ not used in the translation, are considered meta-info
        #        for the Control Device
        #      ~ meta-info keys are added to the `info` dictionary
        #        attribute that is bound to the numpy array data object
        #        constructed by hdfReadControl
        #
        # TODO: add assertion of sub-dict value format
        self.assertIsInstance(_map.configs, dict)
        for config_name, config in _map.configs.items():
            # assert required keys
            # - any other key is considered meta-info and is not used
            #   in the data translation
            #
            self.assertIsInstance(config, dict)
            self.assertIn('dset paths', config)
            self.assertIn('shotnum', config)
            self.assertIn('state values', config)
            if _map.has_command_list:
                self.assertIn('command list', config)

                # check 'command list'
                self.assertIsInstance(config['command list'], tuple)
                self.assertNotEqual(len(config['command list']), 0)
                self.assertTrue(all(
                    isinstance(command, str)
                    for command in config['command list']))

            # check 'dset paths' key
            self.assertIsInstance(config['dset paths'], str)

            # check 'shotnum' features
            # ~ required keys ~
            self.assertIsInstance(config['shotnum'], dict)
            self.assertIn('dset paths', config['shotnum'])
            self.assertIn('dset field', config['shotnum'])
            self.assertIn('shape', config['shotnum'])
            self.assertIn('dtype', config['shotnum'])

            # ~ 'dset paths' key ~
            self.assertEqual(config['shotnum']['dset paths'],
                             config['dset paths'])

            # ~ 'dset field' key ~
            self.assertIsInstance(
                config['shotnum']['dset field'], tuple)
            self.assertEqual(len(config['shotnum']['dset field']), 1)
            self.assertIsInstance(
                config['shotnum']['dset field'][0], str)

            # ~ 'shape' key ~
            self.assertIsInstance(config['shotnum']['shape'], tuple)
            self.assertEqual(config['shotnum']['shape'], ())

            # ~ 'dtype' key ~
            self.assertEqual(config['shotnum']['dtype'], np.int32)

            # check 'state values' features
            self.assertIsInstance(config['state values'], dict)
            for pstate_dict in config['state values'].values():
                # required keys
                self.assertIsInstance(pstate_dict, dict)
                self.assertIn('dset paths', pstate_dict)
                self.assertIn('dset field', pstate_dict)
                self.assertIn('shape', pstate_dict)
                self.assertIn('dtype', pstate_dict)

                # 'dset paths' key
                self.assertEqual(pstate_dict['dset paths'],
                                 config['dset paths'])

                # 'dset field' key
                self.assertIsInstance(
                    pstate_dict['dset field'], tuple)
                self. assertNotEqual(len(pstate_dict['dset field']), 0)
                self.assertTrue(all(
                    isinstance(field, str)
                    for field in pstate_dict['dset field']))

                # 'shape' key
                self.assertIsInstance(pstate_dict['shape'], tuple)
                if len(pstate_dict['shape']) == 0:
                    self.assertEqual(len(pstate_dict['dset field']), 1)
                else:
                    self.assertIn(len(pstate_dict['dset field']),
                                  (1, pstate_dict['shape'][0]))

                # 'dtype' key
                # - 'dtype' must be convertible by np.dtype
                # TODO: ?? IS THIS THE CORRECT WAY
                np.dtype(pstate_dict['dtype'])

                # for command list control devices
                # TODO: ADD MORE DETAIL TO TESTS
                if _map.has_command_list:
                    self.assertIn('command list', pstate_dict)
                    self.assertIn('cl str', pstate_dict)
                    self.assertIn('re pattern', pstate_dict)

                    # check 'command list'
                    # - the matched 'command list' value
                    self.assertIsInstance(pstate_dict['command list'],
                                          tuple)
                    self.assertEqual(len(pstate_dict['command list']),
                                     len(config['command list']))
                    self.assertTrue(all(
                        isinstance(command,
                                   type(pstate_dict['command list'][0]))
                        for command in pstate_dict['command list']))

                    # check 'cl str'
                    # - the resulting string from the RE
                    self.assertIsInstance(pstate_dict['cl str'],
                                          tuple)
                    self.assertEqual(len(pstate_dict['cl str']),
                                     len(config['command list']))
                    self.assertTrue(all(
                        isinstance(clstr, str)
                        for clstr in pstate_dict['cl str']))

                    # check 're pattern'
                    # - the RE pattern used for matching against the
                    #   original command list
                    self.assertIsInstance(
                        pstate_dict['re pattern'],
                        (type(None), type(re.compile(r''))))

    def assertSubgroupNames(self, _map, _group):
        sgroup_names = [name
                        for name in _group
                        if isinstance(_group[name], h5py.Group)]
        self.assertEqual(_map.subgroup_names, sgroup_names)

    def assertDatasetNames(self, _map, _group):
        dset_names = [name
                      for name in _group
                      if isinstance(_group[name], h5py.Dataset)]
        self.assertEqual(_map.dataset_names, dset_names)
