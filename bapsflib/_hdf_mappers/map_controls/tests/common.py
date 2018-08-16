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
from ..control_template import (hdfMap_control_template,
                                hdfMap_control_cl_template)

import os
import re
import h5py

import numpy as np
import unittest as ut


class ControlTestCase(ut.TestCase):
    """
    TestCase for control devices.
    """
    def assertControlMapBasics(self, cmap, cgroup):
        # check mapping instance
        self.assertIsInstance(cmap, hdfMap_control_template)

        # assert attribute existence
        self.assertTrue(hasattr(cmap, 'info'))
        self.assertTrue(hasattr(cmap, 'configs'))
        self.assertTrue(hasattr(cmap, 'contype'))
        self.assertTrue(hasattr(cmap, 'name'))
        self.assertTrue(hasattr(cmap, 'group'))
        self.assertTrue(hasattr(cmap, 'sgroup_names'))
        self.assertTrue(hasattr(cmap, 'dataset_names'))
        self.assertTrue(hasattr(cmap, 'has_command_list'))
        self.assertTrue(hasattr(cmap, 'one_config_per_dset'))
        self.assertTrue(hasattr(cmap, 'construct_dataset_name'))
        self.assertTrue(hasattr(cmap, 'build_successful'))

        # extra attributes for a command list (CL) focused device
        self.assertIsInstance(cmap.has_command_list, bool)
        if cmap.has_command_list:
            # check inherited form proper template
            self.assertIsInstance(cmap, hdfMap_control_cl_template)

            # assert CL attributes
            self.assertTrue(hasattr(cmap, '_cl_re_patterns'))
            self.assertTrue(hasattr(cmap,
                                    '_default_state_values_dict'))
            self.assertTrue(hasattr(cmap,
                                    '_construct_state_values_dict'))
            self.assertTrue(hasattr(cmap, 'clparse'))
            self.assertTrue(hasattr(cmap, 'reset_state_values_config'))
            self.assertTrue(hasattr(cmap, 'set_state_values_config'))

        # ---- test map.info                                        ----
        # test 'info' type
        self.assertIsInstance(cmap.info, dict)

        # check 'info' keys
        self.assertIn('group name', cmap.info)
        self.assertIn('group path', cmap.info)
        self.assertIn('contype', cmap.info)

        # check 'info' values
        self.assertEqual(cmap.info['group name'],
                         os.path.basename(cgroup.name))
        self.assertEqual(cmap.info['group path'], cgroup.name)
        self.assertIn(cmap.info['contype'],
                      ['motion', 'waveform', 'power', 'timing',
                       'generic'])

        # ---- test general attributes                              ----
        # check 'contype'
        self.assertEqual(cmap.info['contype'], cmap.contype)

        # check 'name'
        self.assertEqual(cmap.name, cmap.info['group name'])

        # check 'group'
        self.assertIsInstance(cmap.group, h5py.Group)
        self.assertEqual(cmap.group, cgroup)

        # check 'sgroup_names' (sub-group names)
        self.assertSubgroupNames(cmap, cgroup)

        # check 'dataset_names'
        self.assertDatasetNames(cmap, cgroup)

        # check 'one_config_per_dset'
        self.assertIsInstance(cmap.one_config_per_dset, bool)

        # check 'build_successful'
        # - all assertions below will only pass if build was successful
        self.assertIsInstance(cmap.build_successful, bool)
        self.assertTrue(cmap.build_successful)

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
        self.assertIsInstance(cmap.configs, dict)
        for config_name, config in cmap.configs.items():
            # assert required keys
            # - any other key is considered meta-info and is not used
            #   in the data translation
            #
            self.assertIsInstance(config, dict)
            self.assertIn('dset paths', config)
            self.assertIn('shotnum', config)
            self.assertIn('state values', config)
            if cmap.has_command_list:
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
                if cmap.has_command_list:
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

    def assertSubgroupNames(self, cmap, cgroup):
        sgroup_names = [name
                        for name in cgroup
                        if isinstance(cgroup[name], h5py.Group)]
        self.assertEqual(cmap.sgroup_names, sgroup_names)

    def assertDatasetNames(self, cmap, cgroup):
        dset_names = [name
                      for name in cgroup
                      if isinstance(cgroup[name], h5py.Dataset)]
        self.assertEqual(cmap.dataset_names, dset_names)
