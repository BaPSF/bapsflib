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
import tempfile
import h5py
import shutil


class HDFTestCase(ut.TestCase):
    """
    Base test class for unit testing of HDF5 focused routines.
    """
    @classmethod
    def setUpClass(cls):
        # cls.tempdir = tempfile.mkdtemp(prefix='hdf-test_')
        cls.tempdir = tempfile.TemporaryDirectory(prefix='hdf-test_')

    @classmethod
    def setDownClass(cls):
        # shutil.rmtree(cls.tempdir)
        cls.tempdir.cleanup()

    def TempFile(self, suffix='.hdf5', prefix='', dir=None):
        if dir is None:
            dir = self.tempdir
        return tempfile.TemporaryFile(suffix=suffix, prefix=prefix,
                                      dir=dir)

    def setUp(self):
        self.f = h5py.File(self.TempFile(), 'w')

    def setDown(self):
        if self.f:
            self.f.close()
