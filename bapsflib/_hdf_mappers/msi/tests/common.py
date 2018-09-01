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
from ..templates import hdfMap_msi_template

import os
import h5py

import unittest as ut


class MSIDiagnosticTestCase(ut.TestCase):

    def assertMSIDiagMapBasics(self, _map, _group):
        # check mapping instance
        self.assertIsInstance(_map, hdfMap_msi_template)

        # assert attribute existence
        self.assertTrue(hasattr(_map, 'info'))
        self.assertTrue(hasattr(_map, 'device_name'))
        self.assertTrue(hasattr(_map, 'configs'))
        self.assertTrue(hasattr(_map, 'group'))
        self.assertTrue(hasattr(_map, 'build_successful'))

        # ---- test map.info                                        ----
        # test 'info' type
        self.assertIsInstance(_map.info, dict)

        # check 'info' keys
        self.assertIn('group name', _map.info)
        self.assertIn('group path', _map.info)

        # check 'info' values
        self.assertEqual(_map.info['group name'],
                         os.path.basename(_group.name))
        self.assertEqual(_map.info['group path'], _group.name)

        # ---- test map.device_name                             ----
        self.assertEqual(_map.device_name, _map.info['group name'])

        # ---- test map.group                                       ----
        # check 'group' type
        self.assertIsInstance(_map.group, h5py.Group)

        # ---- test map.build_successful                            ----
        # - all assertions below will only pass if build was successful
        self.assertIsInstance(_map.build_successful, bool)
        self.assertTrue(_map.build_successful)

        # ---- test map.configs                                     ----
        # - must be a dict
        # TODO: write once format is pinned down
        self.assertIsInstance(_map.configs, dict)

        # look for required keys
        self.assertIn('shape', _map.configs)
        self.assertIn('shotnum', _map.configs)
        self.assertIn('signals', _map.configs)
        self.assertIn('meta', _map.configs)

        # inspect non-required keys
        # TODO: IS INSPECTION OF NON-REQUIRED KEYS NEEDED

        # examine 'shotnum' key
        self.assertIsInstance(_map.configs['shotnum'], dict)
        self.assertIn('dset paths', _map.configs['shotnum'])
        self.assertIn('dset field', _map.configs['shotnum'])
        self.assertIn('shape', _map.configs['shotnum'])
        self.assertIn('dtype', _map.configs['shotnum'])
        self.assertIsInstance(
            _map.configs['shotnum']['dset paths'], list)
        self.assertTrue(
            all([isinstance(path, str)
                 for path in _map.configs['shotnum']['dset paths']]))
        self.assertIsInstance(
            _map.configs['shotnum']['shape'], list)
        self.assertTrue(
            all([isinstance(shape, tuple)
                 for shape in _map.configs['shotnum']['shape']]))

        # examine 'signals' key
        self.assertIsInstance(_map.configs['signals'], dict)
        for field in _map.configs['signals']:
            self.assertIsInstance(_map.configs['signals'][field], dict)
            self.assertIn('dset paths', _map.configs['signals'][field])
            self.assertIn('dset field', _map.configs['signals'][field])
            self.assertIn('shape', _map.configs['signals'][field])
            self.assertIn('dtype', _map.configs['signals'][field])

            # 'dset paths'
            self.assertIsInstance(
                _map.configs['signals'][field]['dset paths'], list)
            self.assertTrue(
                all([isinstance(path, str)
                     for path in
                     _map.configs['signals'][field]['dset paths']]))

            # 'shape'
            self.assertIsInstance(
                _map.configs['signals'][field]['shape'], list)
            self.assertTrue(all(
                [isinstance(shape, tuple)
                 for shape in _map.configs['signals'][field]['shape']]
            ))

        # examine 'meta' key
        self.assertIsInstance(_map.configs['meta'], dict)
        self.assertIn('shape', _map.configs['meta'])
        for field in _map.configs['meta']:
            if field == 'shape':
                # key 'shape' will not be a numpy field, skip below
                # assertions
                continue

            # examine each sub-field in 'meta'
            self.assertIsInstance(_map.configs['meta'][field], dict)
            self.assertIn('dset paths', _map.configs['meta'][field])
            self.assertIn('dset field', _map.configs['meta'][field])
            self.assertIn('shape', _map.configs['meta'][field])
            self.assertIn('dtype', _map.configs['meta'][field])

            # 'dset paths'
            self.assertIsInstance(
                _map.configs['meta'][field]['dset paths'], list)
            self.assertTrue(
                all([isinstance(path, str)
                     for path in
                     _map.configs['meta'][field]['dset paths']]))

            # 'shape'
            self.assertIsInstance(
                _map.configs['meta'][field]['shape'], list)
            self.assertTrue(all(
                [isinstance(shape, tuple)
                 for shape in _map.configs['meta'][field]['shape']]
            ))
