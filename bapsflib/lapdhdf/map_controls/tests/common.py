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
import unittest as ut
import h5py


class ControlTestCase(ut.TestCase):

    def assertControlMapBasics(self, map):
        # assert attribute existence
        self.assertTrue(hasattr(map, 'info'))
        self.assertTrue(hasattr(map, 'configs'))
        self.assertTrue(hasattr(map, 'contype'))
        self.assertTrue(hasattr(map, 'dataset_names'))
        self.assertTrue(hasattr(map, 'group'))
        self.assertTrue(hasattr(map, 'has_command_list'))
        self.assertTrue(hasattr(map, 'one_config_per_dset'))
        self.assertTrue(hasattr(map, 'sgroup_names'))
        self.assertTrue(hasattr(map, 'name'))
        self.assertTrue(hasattr(map, 'construct_dataset_name'))
        self.assertTrue(hasattr(map, 'unique_specifiers'))

        # test type and keys for map.info
        self.assertIsInstance(map.info, dict)
        self.assertIn('group name', map.info)
        self.assertIn('group path', map.info)
        self.assertIn('contype', map.info)

        # test type for map.configs
        self.assertIsInstance(map.configs, dict)

        # assert contype
        self.assertEqual(map.info['contype'], map.contype)

        # assert attribute 'group' type
        self.assertIsInstance(map.group, h5py.Group)

        # test attribute 'unique_specifiers'
        self.assertListEqual(list(map.configs), map.unique_specifiers)
