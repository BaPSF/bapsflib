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
    _KNOWN_MSI = {}
    _KNOWN_DIGITIZERS = {}
    _KNOWN_CONTROLS = {'Waveform': FauxWaveform}
    _KNOWN_MODULES = _KNOWN_CONTROLS.copy()
    _KNOWN_MODULES.update(_KNOWN_MSI)
    _KNOWN_MODULES.update(_KNOWN_DIGITIZERS)

    def __init__(self, name=None, add_modules=None, **kwargs):
        # define file name, directory, and path
        if name is None:
            # create temporary directory and file
            self._tempdir = \
                tempfile.TemporaryDirectory(prefix='hdf-test_')
            self._tempfile = \
                tempfile.NamedTemporaryFile(suffix='.hdf5',
                                            dir=self.tempdir.name,
                                            delete=False)
            self._path = self.tempfile.name
        else:
            # use specified directory and file
            self._tempdir = None
            self._tempfile = None
            self._path = name

        # initialize
        h5py.File.__init__(self, self.path, 'w')

        # create root groups
        self.create_group('MSI')
        self.create_group('Raw data + config/')

        # add waveform
        self._modules = {}
        try:
            # add modules if known
            for key, val in add_modules.items():
                if key in self._KNOWN_MODULES:
                    self._add_module(key, val)

        except TypeError:
            # add nothing if add_modules == None
            if add_modules is not None:
                self.cleanup()
                raise ValueError
        except (ValueError, AttributeError):
            self.cleanup()
            raise ValueError(
                "add_modules must be a dictionary of dictionaries..."
                "{'mod_name': mod_inputs}")

    @property
    def modules(self):
        """
        Dictionary containing the module objects associated with the
        added modules.
        """
        return self._modules

    @property
    def tempdir(self):
        """
        Temporary directory containing :attr:`tempfile`.  :code:`None`
        if a real directory is specified upon creation.
        """
        return self._tempdir

    @property
    def tempfile(self):
        """
        Temporary HDF5 file. :code:`None` if a real file is specified
        upon creation.
        """
        return self._tempfile

    @property
    def path(self):
        """Path to HDF5 file"""
        return self._path

    def cleanup(self):
        """
        Close the HDF5 file and cleanup any temporary directories and
        files.
        """
        # close HDF5 file object
        self.close()

        # cleanup temporary direcotry and file
        if isinstance(self.tempdir, tempfile.TemporaryDirectory):
            self.tempfile.close()
            os.unlink(self.tempfile.name)
            self.tempdir.cleanup()

    def _add_module(self, mod_name, mod_inputs):
        """
        Adds all the groups and datasets to the HDF5 file for the
        requested module.

        :param str mod_name: name of module (e.g. :code:`'Waveform'`)
        :param dict mod_inputs: dictionary of input arguments for the
            module adder
        """
        # determine appropriate root directory for module type
        if mod_name in self._KNOWN_MSI:
            # for MSI diagnostics
            root_dir = 'MSI'
        else:
            # for digitizers and control devices
            root_dir = 'Raw data + config'

        # condition arguments for the module adder
        if isinstance(mod_inputs, dict):
            mod_inputs.update({'id': self[root_dir].id})
        else:
            mod_inputs = {'id': self[root_dir].id}

        # add requested module
        self._modules[mod_name] = \
            self._KNOWN_MODULES[mod_name](**mod_inputs)
