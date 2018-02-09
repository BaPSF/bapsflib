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

    def assertControlMapBasics(self, cmap, cgroup):
        # assert attribute existence
        self.assertTrue(hasattr(cmap, 'info'))
        self.assertTrue(hasattr(cmap, 'configs'))
        self.assertTrue(hasattr(cmap, 'contype'))
        self.assertTrue(hasattr(cmap, 'dataset_names'))
        self.assertTrue(hasattr(cmap, 'group'))
        self.assertTrue(hasattr(cmap, 'has_command_list'))
        self.assertTrue(hasattr(cmap, 'one_config_per_dset'))
        self.assertTrue(hasattr(cmap, 'sgroup_names'))
        self.assertTrue(hasattr(cmap, 'name'))
        self.assertTrue(hasattr(cmap, 'construct_dataset_name'))
        self.assertTrue(hasattr(cmap, 'unique_specifiers'))

        # test type and keys for map.info
        self.assertIsInstance(cmap.info, dict)
        self.assertIn('group name', cmap.info)
        self.assertIn('group path', cmap.info)
        self.assertIn('contype', cmap.info)

        # test map.configs
        # - must be a dict
        # - each key must have a dict value
        # - each sub-dict must have certain keys
        # TODO: add assertion of sub-dict value format
        self.assertIsInstance(cmap.configs, dict)
        for config in cmap.configs:
            self.assertIsInstance(cmap.configs[config], dict)
            self.assertIn('dataset fields', cmap.configs[config])
            self.assertIn('dset field to numpy field',
                          cmap.configs[config])

        # assert contype
        self.assertEqual(cmap.info['contype'], cmap.contype)

        # assert attribute 'group' type
        self.assertIsInstance(cmap.group, h5py.Group)

        # test attribute 'unique_specifiers'
        self.assertListEqual(list(cmap.configs), cmap.unique_specifiers)

        # test all sub-group names
        self.assertSubgroupNames(cmap, cgroup)

    def assertSubgroupNames(self, cmap, cgroup):
        sgroup_names = [name
                        for name in cgroup
                        if isinstance(cgroup[name], h5py.Group)]
        self.assertEqual(cmap.sgroup_names, sgroup_names)
