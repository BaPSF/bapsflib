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
from ..msi_template import hdfMap_msi_template

import os
import h5py

import unittest as ut


class MSIDiagnosticTestCase(ut.TestCase):

    def assertMSIDiagMapBasics(self, dmap, dgroup):
        # check mapping instance
        self.assertIsInstance(dmap, hdfMap_msi_template)

        # assert attribute existence
        self.assertTrue(hasattr(dmap, 'info'))
        self.assertTrue(hasattr(dmap, 'device_name'))
        self.assertTrue(hasattr(dmap, 'configs'))
        self.assertTrue(hasattr(dmap, 'group'))
        self.assertTrue(hasattr(dmap, 'build_successful'))

        # ---- test map.info                                        ----
        # test 'info' type
        self.assertIsInstance(dmap.info, dict)

        # check 'info' keys
        self.assertIn('group name', dmap.info)
        self.assertIn('group path', dmap.info)

        # check 'info' values
        self.assertEqual(dmap.info['group name'],
                         os.path.basename(dgroup.name))
        self.assertEqual(dmap.info['group path'], dgroup.name)

        # ---- test map.device_name                             ----
        self.assertEqual(dmap.device_name, dmap.info['group name'])

        # ---- test map.group                                       ----
        # check 'group' type
        self.assertIsInstance(dmap.group, h5py.Group)

        # ---- test map.build_successful                            ----
        # - all assertions below will only pass if build was successful
        self.assertIsInstance(dmap.build_successful, bool)
        self.assertTrue(dmap.build_successful)

        # ---- test map.configs                                     ----
        # - must be a dict
        # TODO: write once format is pinned down
        self.assertIsInstance(dmap.configs, dict)

        # look for required keys
        self.assertIn('shape', dmap.configs)
        self.assertIn('shotnum', dmap.configs)
        self.assertIn('signals', dmap.configs)
        self.assertIn('meta', dmap.configs)

        # inspect non-required keys
        # TODO: IS INSPECTION OF NON-REQUIRED KEYS NEEDED

        # examine 'shotnum' key
        self.assertIsInstance(dmap.configs['shotnum'], dict)
        self.assertIn('dset paths', dmap.configs['shotnum'])
        self.assertIn('dset field', dmap.configs['shotnum'])
        self.assertIn('shape', dmap.configs['shotnum'])
        self.assertIn('dtype', dmap.configs['shotnum'])
        self.assertIsInstance(
            dmap.configs['shotnum']['dset paths'], list)
        self.assertTrue(
            all([isinstance(path, str)
                 for path in dmap.configs['shotnum']['dset paths']]))
        self.assertIsInstance(
            dmap.configs['shotnum']['shape'], list)
        self.assertTrue(
            all([isinstance(shape, tuple)
                 for shape in dmap.configs['shotnum']['shape']]))

        # examine 'signals' key
        self.assertIsInstance(dmap.configs['signals'], dict)
        for field in dmap.configs['signals']:
            self.assertIsInstance(dmap.configs['signals'][field], dict)
            self.assertIn('dset paths', dmap.configs['signals'][field])
            self.assertIn('dset field', dmap.configs['signals'][field])
            self.assertIn('shape', dmap.configs['signals'][field])
            self.assertIn('dtype', dmap.configs['signals'][field])

            # 'dset paths'
            self.assertIsInstance(
                dmap.configs['signals'][field]['dset paths'], list)
            self.assertTrue(
                all([isinstance(path, str)
                     for path in
                     dmap.configs['signals'][field]['dset paths']]))

            # 'shape'
            self.assertIsInstance(
                dmap.configs['signals'][field]['shape'], list)
            self.assertTrue(all(
                [isinstance(shape, tuple)
                 for shape in dmap.configs['signals'][field]['shape']]
            ))

        # examine 'meta' key
        self.assertIsInstance(dmap.configs['meta'], dict)
        self.assertIn('shape', dmap.configs['meta'])
        for field in dmap.configs['meta']:
            if field == 'shape':
                # key 'shape' will not be a numpy field, skip below
                # assertions
                continue

            # examine each sub-field in 'meta'
            self.assertIsInstance(dmap.configs['meta'][field], dict)
            self.assertIn('dset paths', dmap.configs['meta'][field])
            self.assertIn('dset field', dmap.configs['meta'][field])
            self.assertIn('shape', dmap.configs['meta'][field])
            self.assertIn('dtype', dmap.configs['meta'][field])

            # 'dset paths'
            self.assertIsInstance(
                dmap.configs['meta'][field]['dset paths'], list)
            self.assertTrue(
                all([isinstance(path, str)
                     for path in
                     dmap.configs['meta'][field]['dset paths']]))

            # 'shape'
            self.assertIsInstance(
                dmap.configs['meta'][field]['shape'], list)
            self.assertTrue(all(
                [isinstance(shape, tuple)
                 for shape in dmap.configs['meta'][field]['shape']]
            ))
