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


class MSIDiagnosticTestCase(ut.TestCase):

    def assertMSIDiagMapBasics(self, dmap, dgroup):
        # assert attribute existence
        self.assertTrue(hasattr(dmap, 'info'))
        self.assertTrue(hasattr(dmap, 'configs'))
        self.assertTrue(hasattr(dmap, 'group'))

        # test type and keys for map.info
        self.assertIsInstance(dmap.info, dict)
        self.assertIn('group name', dmap.info)
        self.assertIn('group path', dmap.info)

        # assert attribute 'group' type
        self.assertIsInstance(dmap.group, h5py.Group)

        # test map.configs
        # - must be a dict
        # TODO: write once format is pinned down
        self.assertIsInstance(dmap.configs, dict)
