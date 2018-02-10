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
import numpy as np
import h5py


class DigitizerTestCase(ut.TestCase):

    def assertDigitizerMapBasics(self, dmap, dgroup):
        # assert attribute existence
        self.assertTrue(hasattr(dmap, 'info'))
        self.assertTrue(hasattr(dmap, 'configs'))
        self.assertTrue(hasattr(dmap, 'active_configs'))
        self.assertTrue(hasattr(dmap, 'group'))
        self.assertTrue(hasattr(dmap, 'construct_dataset_name'))

        # test type and keys for map.info
        self.assertIsInstance(dmap.info, dict)
        self.assertIn('group name', dmap.info)
        self.assertIn('group path', dmap.info)

        # test map.configs
        # - must be a dict
        # - each key must have a dict value
        # - each sub-dict must have certain keys
        self.assertIsInstance(dmap.configs, dict)
        for config in dmap.configs:
            self.assertIsInstance(dmap.configs[config], dict)
            self.assertIn('active', dmap.configs[config])
            self.assertIn('adc', dmap.configs[config])
            self.assertIn('group name', dmap.configs[config])
            self.assertIn('group path', dmap.configs[config])

            # check types
            self.assertIsInstance(dmap.configs[config]['active'], bool)
            self.assertIsInstance(dmap.configs[config]['adc'], list)
            self.assertIsInstance(
                dmap.configs[config]['group name'], str)
            self.assertIsInstance(
                dmap.configs[config]['group path'], str)

            # test adc details
            for adc in dmap.configs[config]['adc']:
                self.assertIn(adc, dmap.configs[config])
                self.assertIsInstance(dmap.configs[config][adc], list)

                for item in dmap.configs[config][adc]:
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
                    self.assertIn('sample rate', item[2])
                    self.assertIn('shot average (software)', item[2])
                    self.assertIn('sample average (hardware)', item[2])

        # assert attribute 'group' type
        self.assertIsInstance(dmap.group, h5py.Group)
