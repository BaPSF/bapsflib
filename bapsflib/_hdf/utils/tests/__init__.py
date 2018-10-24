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

from bapsflib._hdf.maps import FauxHDFBuilder

from ..file import File


class TestBase(ut.TestCase):
    """Base test class for all test classes here."""

    f = NotImplemented   # type: FauxHDFBuilder

    @classmethod
    def setUpClass(cls):
        # create HDF5 file
        super().setUpClass()
        cls.f = FauxHDFBuilder()

    def tearDown(self):
        self.f.remove_all_modules()

    @classmethod
    def tearDownClass(cls):
        # cleanup and close HDF5 file
        super().tearDownClass()
        cls.f.cleanup()

    @property
    def bf(self) -> File:
        """Opened BaPSF HDF5 File instance."""
        return File(self.f.filename, control_path='Raw data + config',
                    digitizer_path='Raw data + config', msi_path='MSI')
