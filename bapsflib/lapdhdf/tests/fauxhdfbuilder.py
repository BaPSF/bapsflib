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
import inspect

from ..map_controls.tests import FauxWaveform
from ..map_controls.tests import FauxSixK
from ..map_digitizers.tests import FauxSIS3301


class FauxHDFBuilder(h5py.File):
    """
    Builds a Faux HDF5 file that simulates a HDF5 build by the LaPD.
    """
    _KNOWN_MSI = {}
    _KNOWN_DIGITIZERS = {'SIS 3301': FauxSIS3301}
    _KNOWN_CONTROLS = {'Waveform': FauxWaveform,
                       '6K Compumotor': FauxSixK}
    _KNOWN_MODULES = _KNOWN_CONTROLS.copy()
    _KNOWN_MODULES.update(_KNOWN_MSI)
    _KNOWN_MODULES.update(_KNOWN_DIGITIZERS)

    def __init__(self, name=None, add_modules=None, **kwargs):
        """
        :param str name: name of HDF5 file
        :param add_modules:
        :param kwargs:
        """
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

        # create file attributes
        self.attrs['LaPD HDF5 software version'] = b'0.0.0'

        # create MSI attributes
        # - none at the moment
        self['Raw data + config'].attrs['Description'] = \
            b'some description'

        # create 'Raw data + config' attributes

        # add waveform
        self._modules = {}
        try:
            # add modules if known
            if add_modules is not None:
                for key, val in add_modules.items():
                    if key in self._KNOWN_MODULES:
                        self.add_module(key, val)

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

    def valid_modules(self):
        """
        List of valid modules and their input arguments. For
        example,::

            valid_modules = [
                {'name': 'Waveform',
                 'args': {'n_configs': 1, 'sn_size': 100}},
            ]
        """
        # gather mod_name and mod_args
        vmods = []
        mod_args = {}
        for mod_name in self._KNOWN_MODULES:
            sign = inspect.signature(self._KNOWN_MODULES[mod_name])
            for arg_name in sign.parameters:
                if arg_name != 'id' and arg_name != 'kwargs':
                    # do not add h5py.GroupID and kwargs arguments to
                    # dictionary
                    mod_args[arg_name] = \
                        sign.parameters[arg_name].default

            # build dict
            vmods.append({'name': mod_name,
                          'args': mod_args.copy()})
            mod_args.clear()

        # return valid modules
        return vmods

    def add_module(self, mod_name, mod_args=None):
        """
        Adds all the groups and datasets to the HDF5 file for the
        requested module.

        :param str mod_name: name of module (e.g. :code:`'Waveform'`)
        :param dict mod_args: dictionary of input arguments for the
            module adder
        """
        if mod_name not in self._KNOWN_MODULES:
            # requested module not known
            pass
        elif mod_name in self.modules:
            # requested module already added
            pass
        else:
            # determine appropriate root directory for module type
            if mod_name in self._KNOWN_MSI:
                # for MSI diagnostics
                root_dir = 'MSI'
            else:
                # for digitizers and control devices
                root_dir = 'Raw data + config'

            # condition arguments for the module adder
            if isinstance(mod_args, dict):
                mod_args.update({'id': self[root_dir].id})
            else:
                mod_args = {'id': self[root_dir].id}

            # add requested module
            self._modules[mod_name] = \
                self._KNOWN_MODULES[mod_name](**mod_args)

    def remove_module(self, mod_name):
        """Remove requested module"""
        if mod_name in self._modules:
            mod_path = self._modules[mod_name].name
            del self[mod_path]
            del self._modules[mod_name]

    def remove_all_modules(self):
        """Remove all modules"""
        modules = self._modules
        for mod in modules:
            self.remove_module(mod)
