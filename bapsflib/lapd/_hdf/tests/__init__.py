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
__all__ = ["BaseFile", "TestBase", "with_bf", "with_lapdf"]

import unittest as ut

from bapsflib._hdf import File as BaseFile
from bapsflib._hdf.maps import FauxHDFBuilder
from bapsflib.utils.decorators import with_bf, with_lapdf


def method_overridden(cls, obj, method: str) -> bool:
    """check if obj's class over-road base class method"""
    obj_method = method in obj.__class__.__dict__.keys()
    base_method = method in cls.__dict__.keys()
    return obj_method and base_method


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

    def assertMethodOverride(self, base_class, obj, method):
        """
        Assert the class that instantiated `obj` over-road `base_class`
        `method`.

        :param base_class: the class the was sub-classes
        :param obj: the instantiated object
        :param str method: method that should have been over-written
        """
        self.assertTrue(method_overridden(base_class, obj, method))

    def assertNotMethodOverride(self, base_class, obj, method):
        """
        Assert the class that instantiated `obj` did NOT override
        `base_class` `method`.

        :param base_class: the class the was sub-classes
        :param obj: the instantiated object
        :param str method: method that should have NOT been over-written
        """
        self.assertTrue(method_overridden(base_class, obj, method))

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
