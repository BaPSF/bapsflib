# This file is part of the bapsflib package, a Python toolkit for the
# BaPSF group at UCLA.
#
# http://plasma.physics.ucla.edu/
#
# Copyright 2017-2019 Erik T. Everson and contributors
#
# License: Standard 3-clause BSD; see "LICENSES/LICENSE.txt" for full
#   license terms and contributor agreement.
#
import h5py
import inspect
import os
import platform
import tempfile

from typing import Any, Dict

from bapsflib._hdf.maps.controls.tests import (
    FauxN5700PS,
    FauxNIXYZ,
    FauxNIXZ,
    FauxSixK,
    FauxWaveform,
)
from bapsflib._hdf.maps.digitizers.tests import FauxSIS3301, FauxSISCrate
from bapsflib._hdf.maps.msi.tests import (
    FauxDischarge,
    FauxGasPressure,
    FauxHeater,
    FauxInterferometerArray,
    FauxMagneticField,
)


class FauxHDFBuilder(h5py.File):
    """
    Builds a Faux HDF5 file that simulates a HDF5 constructed at BaPSF.
    """

    _KNOWN_MSI = {
        "Discharge": FauxDischarge,
        "Gas pressure": FauxGasPressure,
        "Heater": FauxHeater,
        "Interferometer array": FauxInterferometerArray,
        "Magnetic field": FauxMagneticField,
    }
    _KNOWN_DIGITIZERS = {
        "SIS 3301": FauxSIS3301,
        "SIS crate": FauxSISCrate,
    }
    _KNOWN_CONTROLS = {
        "6K Compumotor": FauxSixK,
        "N5700_PS": FauxN5700PS,
        "NI_XYZ": FauxNIXYZ,
        "NI_XZ": FauxNIXZ,
        "Waveform": FauxWaveform,
    }
    _KNOWN_MODULES = _KNOWN_CONTROLS.copy()  # type: Dict[Any]
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
            # define NamedTemporaryFile delete
            # - on a Unix platform the file can be opened multiple times
            # - on a Windows platform it can only be opened once
            #   * thus, delete=False needs to be set so the file
            #     persists for play
            delete = False if platform.system() == "Windows" else True

            # create temporary directory and file
            self._tempdir = tempfile.TemporaryDirectory(prefix="hdf-test_")
            self._tempfile = tempfile.NamedTemporaryFile(
                suffix=".hdf5", dir=os.path.abspath(self.tempdir.name), delete=delete
            )
            self._path = os.path.abspath(self.tempfile.name)

            if platform.system() == "Windows":
                # close the file so h5py can access it on a Windows
                # platform
                self._tempfile.close()
        else:
            # use specified directory and file
            self._tempdir = None
            self._tempfile = None
            self._path = os.path.abspath(name)

        # initialize
        h5py.File.__init__(self, self.path, "w")

        # create root groups
        self.create_group("MSI")
        self.create_group("Raw data + config/")

        # create file attributes
        self.attrs["LaPD HDF5 software version"] = b"0.0.0"

        # create MSI attributes
        # - none at the moment
        self["Raw data + config"].attrs["Description"] = b"some description"

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
                "{'mod_name': mod_inputs}"
            )

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

    def close(self):
        """
        Close the HDF5 file and remove temporary files/directories if
        the exist.
        """
        _path = os.path.abspath(self.filename)
        super().close()

        # cleanup temporary directory and file
        if isinstance(self.tempdir, tempfile.TemporaryDirectory):
            if platform.system() == "Windows":
                # tempfile is already closed, need to remove file
                os.remove(_path)
            else:
                self.tempfile.close()
            self.tempdir.cleanup()

    def cleanup(self):
        """
        Close the HDF5 file and cleanup any temporary directories and
        files.
        """
        self.close()

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
                if arg_name != "id" and arg_name != "kwargs":
                    # do not add h5py.GroupID and kwargs arguments to
                    # dictionary
                    mod_args[arg_name] = sign.parameters[arg_name].default

            # build dict
            vmods.append({"name": mod_name, "args": mod_args.copy()})
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
        # TODO: behavior when adding a module that already exists ??
        #
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
                root_dir = "MSI"
            else:
                # for digitizers and control devices
                root_dir = "Raw data + config"

            # condition arguments for the module adder
            if isinstance(mod_args, dict):
                mod_args.update({"id": self[root_dir].id})
            else:
                mod_args = {"id": self[root_dir].id}

            # add requested module
            self._modules[mod_name] = self._KNOWN_MODULES[mod_name](**mod_args)

    def clear_control_modules(self):
        """Remove all control device modules"""
        data_mod_names = list(self["Raw data + config"].keys())
        for mod_name in data_mod_names:
            if mod_name in self._KNOWN_CONTROLS:
                self.remove_module(mod_name)

    def clear_digi_modules(self):
        """Remove all digitizer modules"""
        data_mod_names = list(self["Raw data + config"].keys())
        for mod_name in data_mod_names:
            if mod_name in self._KNOWN_DIGITIZERS:
                self.remove_module(mod_name)

    def clear_msi_modules(self):
        """Remove all MSI modules"""
        msi_mod_names = list(self["MSI"].keys())
        for mod_name in msi_mod_names:
            self.remove_module(mod_name)

    def remove_module(self, mod_name):
        """Remove requested module"""
        if mod_name in self._modules:
            mod_path = self._modules[mod_name].name
            del self[mod_path]
            del self._modules[mod_name]

    def remove_all_modules(self):
        """Remove all modules"""
        modules = list(self._modules.keys())
        for mod in modules:
            self.remove_module(mod)

    def reset(self):
        """
        Restore file such that only empty version of the 'MSI' and
        'Raw data + config' group exist.
        """
        self.remove_all_modules()
        for name in self["MSI"]:
            del self[f"MSI/{name}"]
        for name in self["Raw data + config"]:
            del self[f"Raw data + config/{name}"]
