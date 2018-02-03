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

    @property
    def map(self):
        return NotImplemented

    def test_attributes_generic(self):
        # test for existence
        self.assertTrue(hasattr(self.map, 'info'))
        self.assertTrue(hasattr(self.map, 'configs'))
        self.assertTrue(hasattr(self.map, 'contype'))
        self.assertTrue(hasattr(self.map, 'dataset_names'))
        self.assertTrue(hasattr(self.map, 'group'))
        self.assertTrue(hasattr(self.map, 'has_command_list'))
        self.assertTrue(hasattr(self.map, 'one_config_per_dset'))
        self.assertTrue(hasattr(self.map, 'sgroup_names'))
        self.assertTrue(hasattr(self.map, 'name'))
        self.assertTrue(hasattr(self.map, 'construct_dataset_name'))
        self.assertTrue(hasattr(self.map, 'unique_specifiers'))

        # test type and keys fo map.info
        self.assertIsInstance(self.map.info, dict)
        self.assertIn('group name', self.map.info)
        self.assertIn('group path', self.map.info)
        self.assertIn('contype', self.map.info)

        # test type for map.configs
        self.assertIsInstance(self.map.configs, dict)

    def test_contype(self):
        self.assertEqual(self.map.info['contype'], self.map.contype)

    def test_group(self):
        self.assertIsInstance(self.map.group, h5py.Group)

    def test_unique_specifiers(self):
        self.assertListEqual(list(self.map.configs),
                             self.map.unique_specifiers)
