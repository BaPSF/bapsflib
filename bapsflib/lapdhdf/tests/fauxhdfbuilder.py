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
import h5py
import tempfile
import os

from ..map_controls.tests import FauxWaveform

class FauxHDFBuilder(h5py.File):
    """
    Builds a Faux HDF5 file that simulates a HDF5 build by the LaPD.
    """
    _KNOWN_MODULES = {'waveform': FauxWaveform}

    def __init__(self, add_modules=None, name=None, **kwargs):
        if name is None:
            self._tempdir = \
                tempfile.TemporaryDirectory(prefix='hdf-test_')
            self._tempfile = \
                tempfile.NamedTemporaryFile(suffix='.hdf5',
                                            dir=self.tempdir.name,
                                            delete=False)
            self._path = self.tempfile.name
            head, tail = os.path.split(self._path)
        else:
            self._tempdir = None
            self._tempfile = None
            self._path = name
            head, tail = os.path.split(name)

        h5py.File.__init__(self, self.path, 'w')

        # create root groups
        self.create_group('MSI')
        self.create_group('Raw data + config/')

        # add waveform
        self._modules = {}
        self._modules['waveform'] = \
            FauxWaveform(self['Raw data + config'].id)

    @property
    def modules(self):
        return self._modules

    @property
    def tempdir(self):
        return self._tempdir

    @property
    def tempfile(self):
        return self._tempfile

    @property
    def path(self):
        return self._path

    def cleanup(self):
        self.close()
        if isinstance(self.tempdir, tempfile.TemporaryDirectory):
            self.tempfile.close()
            os.unlink(self.tempfile.name)
            self.tempdir.cleanup()
