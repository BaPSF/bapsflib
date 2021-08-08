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
__all__ = ["TestBase", "with_bf"]

import unittest as ut

from bapsflib._hdf.maps import FauxHDFBuilder
from bapsflib.utils.decorators import with_bf


class TestBase(ut.TestCase):
    """Base test class for all test classes here."""

    f = NotImplemented  # type: FauxHDFBuilder

    @classmethod
    def setUpClass(cls):
        # create HDF5 file
        super().setUpClass()
        cls.f = FauxHDFBuilder()

    def tearDown(self):
        self.f.reset()

    @classmethod
    def tearDownClass(cls):
        # cleanup and close HDF5 file
        super().tearDownClass()
        cls.f.cleanup()

    @property
    def filename(self) -> str:
        return self.f.filename

    @property
    def control_path(self) -> str:
        return "Raw data + config"

    @property
    def digitizer_path(self) -> str:
        return "Raw data + config"

    @property
    def msi_path(self) -> str:
        return "MSI"
